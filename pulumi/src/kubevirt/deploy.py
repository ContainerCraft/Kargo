import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from src.lib.namespace import create_namespace

def deploy_kubevirt(
        ns_name: str,
        version: str,
        k8s_provider: k8s.Provider,
        kubernetes_distribution: str,
        cert_manager: pulumi.Output = None
    ):

    # Create namespace
    ns_retain = True
    ns_protect = False
    namespace = create_namespace(
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider
    )

    # Fetch the latest stable version of KubeVirt
    if version is None:
        kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
        version = requests.get(kubevirt_stable_version_url).text.strip()
        pulumi.log.info(f"Setting version to latest stable: kubevirt/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using KubeVirt version: kubevirt/{version}")

    # Define the transformation to remove Namespace creation and ensure correct namespace for other resources
    # TODO: fix transformation to remove namespace creation (currently producing duplicate namespace resource)
    def remove_namespace_transform(args):
        if args['kind'] == "Namespace":
            pulumi.log.info(f"Skipping creation of duplicate Namespace: {args['metadata']['name']}")
            return None  # Skip the creation of this resource if it's a duplicate
        else:
            if 'metadata' in args:
                args['metadata']['namespace'] = ns_name
        pulumi.log.info(f"Transforming resource of namespace/kind: {ns_name}/{args['kind']}")
        return args

    # Deploy the KubeVirt operator with transformations
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    operator = k8s.yaml.ConfigFile(
        'kubevirt-operator',
        file=kubevirt_operator_url,
        transformations=[remove_namespace_transform],
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=[cert_manager]
        )
    )

    # Determine useEmulation based on the kubernetes_distribution
    use_emulation = True if kubernetes_distribution == "kind" else False
    if use_emulation:
        pulumi.log.info("Using emulation for KubeVirt in developer mode")

    # Create the KubeVirt custom resource object
    kubevirt_custom_resource_spec = {
        "customizeComponents": {},
        "workloadUpdateStrategy": {},
        "certificateRotateStrategy": {},
        "imagePullPolicy": "IfNotPresent",
        "configuration": {
            "smbios": {
                "sku": "kargo-kc2",
                "version": version,
                "manufacturer": "ContainerCraft",
                "product": "Kargo",
                "family": "CCIO"
            },
            "developerConfiguration": {
                "useEmulation": kubernetes_distribution == "kind",
                "featureGates": [
                    "HostDevices",
                    "AutoResourceLimitsGate"
                ]
            },
            "permittedHostDevices": {
                "pciHostDevices": [
                ]
            }
        }
    }

    # Create the KubeVirt custom resource
    kubevirt = CustomResource(
        "kubevirt",
        api_version="kubevirt.io/v1",
        kind="KubeVirt",
        metadata=ObjectMetaArgs(
            name="kubevirt",
            namespace=namespace
        ),
        spec=kubevirt_custom_resource_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=operator,
            depends_on=[
                namespace,
                cert_manager
            ]
        )
    )

    return version, operator

# 🐋 ❯ k get ns -oyaml kubevirt
# apiVersion: v1
# kind: Namespace
# metadata:
#   creationTimestamp: "2024-05-13T21:50:13Z"
#   labels:
#     ccio.v1/app: kargo
#     kubernetes.io/metadata.name: kubevirt
#     kubevirt.io: ""
#     openshift.io/cluster-monitoring: "true"
#     pod-security.kubernetes.io/enforce: privileged
#   name: kubevirt
#   resourceVersion: "1992"
#   uid: ab0fa472-080c-46f5-8c2e-a14988c03c87
# spec:
#   finalizers:
#   - kubernetes
# status:
#   phase: Active
