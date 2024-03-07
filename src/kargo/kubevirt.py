import pulumi
import pulumi_kubernetes as k8s
import requests
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

def deploy_kubevirt(k8s_provider: k8s.Provider):
    """
    Fetches the latest stable version of KubeVirt, deploys the KubeVirt operator,
    the default KubeVirt custom resource, and a detailed KubeVirt custom resource
    using the fetched version.

    :param k8s_provider: A Pulumi Kubernetes provider.
    :return: The version of KubeVirt that was deployed.
    """

    # Fetch the latest stable version of KubeVirt
    kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
    kubevirt_version = requests.get(kubevirt_stable_version_url).text.strip()

    # Deploy the KubeVirt operator
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/{kubevirt_version}/kubevirt-operator.yaml'
    k8s.yaml.ConfigFile(
        'kubevirt-operator',
        file=kubevirt_operator_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Deploy the KubeVirt Custom Resource (default)
    kubevirt_cr_url = f'https://github.com/kubevirt/kubevirt/releases/download/{kubevirt_version}/kubevirt-cr.yaml'
    k8s.yaml.ConfigFile(
        'kubevirt-cr',
        file=kubevirt_cr_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Define and deploy the detailed KubeVirt custom resource
    kubevirt_detailed_manifest = {
        "apiVersion": "kubevirt.io/v1",
        "kind": "KubeVirt",
        "metadata": {
            "name": "kubevirt",
            "namespace": "kubevirt"
        },
        "spec": {
            "customizeComponents": {},
            "workloadUpdateStrategy": {},
            "certificateRotateStrategy": {},
            "imagePullPolicy": "IfNotPresent",
            "configuration": {
                "smbios": {
                    "sku": "kargo-kc2",
                    "version": "v0.1.0",
                    "manufacturer": "ContainerCraft",
                    "product": "Kargo",
                    "family": "CCIO"
                },
                "developerConfiguration": {
                    "featureGates": [
                        "HostDevices"
                    ]
                },
                "permittedHostDevices": {
                    "pciHostDevices": [
                        {
                            "pciVendorSelector": "10de:1c31",
                            "resourceName": "gpu.nvidia.com/P2200quadro"
                        },
                        {
                            "pciVendorSelector": "10de:131b",
                            "resourceName": "gpu.nvidia.com/P2200sub"
                        },
                        {
                            "pciVendorSelector": "10de:10f1",
                            "resourceName": "audio.nvidia.com/P2200quadro"
                        },
                        {
                            "pciVendorSelector": "10de:131b",
                            "resourceName": "audio.nvidia.com/P2200sub"
                        },
                        {
                            "pciVendorSelector": "1002:6995",
                            "resourceName": "vga.amd.com/wx2100pro"
                        },
                        {
                            "pciVendorSelector": "1028:0b0c",
                            "resourceName": "vga.amd.com/wx2100sub"
                        },
                        {
                            "pciVendorSelector": "1002:aae0",
                            "resourceName": "audio.amd.com/wx2100pro"
                        },
                        {
                            "pciVendorSelector": "1028:aae0",
                            "resourceName": "audio.amd.com/wx2100sub"
                        }
                    ]
                }
            }
        }
    }

    kubevirt_detailed = CustomResource(
        "kubevirt-detailed",
        api_version="kubevirt.io/v1",
        kind="KubeVirt",
        metadata=ObjectMetaArgs(
            name="kubevirt",
            namespace="kubevirt"
        ),
        spec=kubevirt_detailed_manifest["spec"],
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return kubevirt_version
