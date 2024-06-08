import requests
import yaml
import tempfile
import os
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from src.lib.namespace import create_namespace

def deploy_kubevirt(
        depends,
        ns_name: str,
        version: str,
        k8s_provider: k8s.Provider,
        kubernetes_distribution: str
    ):

    # Create namespace
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubevirt.io": "",
        "kubernetes.io/metadata.name": ns_name,
        "openshift.io/cluster-monitoring": "true",
        "pod-security.kubernetes.io/enforce": "privileged"
    }
    namespace = create_namespace(
        depends,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        custom_labels=ns_labels,
        custom_annotations=ns_annotations
    )

    # Fetch the latest stable version of KubeVirt
    if version is None:
        kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
        version = requests.get(kubevirt_stable_version_url).text.strip()
        version = version.lstrip("v")
        pulumi.log.info(f"Setting version to latest stable: kubevirt/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using KubeVirt version: kubevirt/{version}")

    # Download the KubeVirt operator YAML
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    response = requests.get(kubevirt_operator_url)
    kubevirt_yaml = yaml.safe_load_all(response.text)

    # Edit the YAML in memory to remove the Namespace and adjust other resources
    transformed_yaml = []
    for resource in kubevirt_yaml:
        if resource and resource.get('kind') == 'Namespace':
            pulumi.log.debug(f"Transforming Namespace resource: {resource['metadata']['name']}")
            continue  # Skip adding this namespace to the edited YAML
        if resource and 'metadata' in resource:
            resource['metadata']['namespace'] = ns_name
            pulumi.log.debug(f"Setting namespace for {resource['kind']} to {ns_name}")
        transformed_yaml.append(resource)

    # Write the edited YAML to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    # Ensure the tempfile is closed before passing it to ConfigFile
    temp_file.close()

    # Pass the edited YAML directly to ConfigFile
    operator = k8s.yaml.ConfigFile(
        'kubevirt-operator',
        file=temp_file_path,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=depends
        )
    )

    # Ensure the temporary file is deleted after Pulumi uses it
    pulumi.Output.all().apply(lambda _: os.unlink(temp_file_path))

    # Determine useEmulation based on the kubernetes_distribution
    use_emulation = True if kubernetes_distribution == "kind" else False
    if use_emulation:
        pulumi.log.info("KVM Emulation configured for KubeVirt in development.")

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
                "useEmulation": use_emulation,
                "featureGates": [
                    "HostDevices",
                    "ExpandDisks",
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
            namespace=ns_name,
        ),
        spec=kubevirt_custom_resource_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=operator,
            depends_on=[
                namespace
            ]
        )
    )

    return version, operator
