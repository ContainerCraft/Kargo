import requests
import yaml
import tempfile
import os
import pulumi
from typing import List
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from src.lib.namespace import create_namespace


def deploy_kubevirt(
    depends: List[pulumi.Resource],
    ns_name: str,
    version: str,
    use_emulation: bool,
    k8s_provider: k8s.Provider,
    kubernetes_distribution: str,
):
    """
    Deploy KubeVirt with Talos-specific configuration and SELinux workaround

    Args:
        depends: List of resources this deployment depends on
        ns_name: Namespace to deploy KubeVirt into
        version: Version of KubeVirt to deploy
        use_emulation: Whether to use emulation mode
        k8s_provider: Kubernetes provider instance
        kubernetes_distribution: Type of k8s distribution (kind, talos)

    Returns:
        Tuple containing:
        - KubeVirt version deployed
        - KubeVirt operator deployment
    """

    # Create namespace with required labels for KubeVirt
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubevirt.io": "",
        "kubernetes.io/metadata.name": ns_name,
        "openshift.io/cluster-monitoring": "true",
        "pod-security.kubernetes.io/enforce": "privileged",
    }
    namespace = create_namespace(
        depends,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        custom_labels=ns_labels,
        custom_annotations=ns_annotations,
    )

    # Fetch the latest stable version of KubeVirt if not specified
    if version is None:
        kubevirt_stable_version_url = "https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt"
        version = requests.get(kubevirt_stable_version_url).text.strip()
        version = version.lstrip("v")
        pulumi.log.info(f"Setting version to latest stable: kubevirt/{version}")
    else:
        pulumi.log.info(f"Using helm release version: kubevirt/{version}")

    # Download the KubeVirt operator YAML
    kubevirt_operator_url = f"https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml"
    response = requests.get(kubevirt_operator_url)
    kubevirt_yaml = yaml.safe_load_all(response.text)

    # Transform YAML to set namespace and remove namespace resource
    transformed_yaml = []
    for resource in kubevirt_yaml:
        if resource and resource.get("kind") == "Namespace":
            pulumi.log.debug(
                f"Transforming Namespace resource: {resource['metadata']['name']}"
            )
            continue
        if resource and "metadata" in resource:
            resource["metadata"]["namespace"] = ns_name
            pulumi.log.debug(f"Setting namespace for {resource['kind']} to {ns_name}")
        transformed_yaml.append(resource)

    # Write transformed YAML to temp file
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    # Close temp file before passing to ConfigFile
    temp_file.close()

    # Deploy KubeVirt operator from modified YAML
    operator = k8s.yaml.ConfigFile(
        "kubevirt-operator",
        file=temp_file_path,
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=depends,
            provider=k8s_provider,
        ),
    )

    # Cleanup temp file after use
    pulumi.Output.all().apply(lambda _: os.unlink(temp_file_path))

    # Set emulation mode based on kubernetes distribution
    use_emulation = True if kubernetes_distribution == "kind" else use_emulation
    if use_emulation:
        pulumi.log.info("KVM Emulation configured for KubeVirt in development.")

    # Create the KubeVirt custom resource with configuration
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
                "family": "CCIO",
            },
            "developerConfiguration": {
                "useEmulation": use_emulation,
                "featureGates": [
                    "HostDevices",
                    "ExpandDisks",
                    "AutoResourceLimitsGate",
                    "NetworkBindingPlugins",
                    "LiveMigration",
                ],
                # Log verbosity levels for KubeVirt components
                # 1-Error, 2-Warn, 3-Info, 4-Debug, 5-Trace
                # 6-TraceAll, 7-DebugAll, 8-InfoAll, 9-WarnAll, 10-ErrorAll
                "logVerbosity": {
                    "virtLauncher": 2,
                    "virtHandler": 3,
                    "virtController": 4,
                    "virtAPI": 5,
                    "virtOperator": 6,
                },
            },
            "permittedHostDevices": {"pciHostDevices": []},
        },
    }

    # Deploy KubeVirt CR
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
            depends_on=depends,
        ),
    )

    # Deploy SELinux workaround DaemonSet for Talos
    selinux_ds = k8s.apps.v1.DaemonSet(
        "disable-selinux",
        metadata={
            "name": "disable-selinux",
            "namespace": ns_name,
            "labels": {"app": "disable-selinux"},
        },
        spec={
            "selector": {"matchLabels": {"app": "disable-selinux"}},
            "template": {
                "metadata": {"labels": {"app": "disable-selinux"}},
                "spec": {
                    "containers": [
                        {
                            "name": "mount",
                            "image": "docker.io/library/alpine",
                            "command": [
                                "sh",
                                "-exc",
                                "test -f  /host/sys/fs/selinux/enforce && mount -t tmpfs tmpfs /host/sys/fs/selinux; sleep infinity",
                            ],
                            "securityContext": {"privileged": True},
                            "volumeMounts": [
                                {
                                    "name": "host-root",
                                    "mountPath": "/host",
                                    "mountPropagation": "Bidirectional",
                                }
                            ],
                        }
                    ],
                    "volumes": [{"name": "host-root", "hostPath": {"path": "/"}}],
                    "hostIPC": True,
                    "hostNetwork": True,
                    "hostPID": True,
                    "tolerations": [{"operator": "Exists"}],
                },
            },
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, parent=namespace, depends_on=[operator]
        ),
    )

    return version, operator
