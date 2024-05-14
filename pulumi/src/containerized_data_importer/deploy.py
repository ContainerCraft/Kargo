import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

def deploy_cdi(version: str, k8s_provider: k8s.Provider):

    # Fetch the latest stable version of CDI
    if version is None:
        tag_url = 'https://github.com/kubevirt/containerized-data-importer/releases/latest'
        tag = requests.get(tag_url, allow_redirects=False).headers.get('location')
        version = tag.split('/')[-1]
        version = version.lstrip('v')
        pulumi.log.info(f"Setting version to latest stable: cdi/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using KubeVirt version: cdi/{version}")

    # Deploy the CDI operator
    cdi_operator_url = f'https://github.com/kubevirt/containerized-data-importer/releases/download/v{version}/cdi-operator.yaml'
    pulumi.log.info(f"Deploying CDI operator from: {cdi_operator_url}")
    operator = k8s.yaml.ConfigFile(
        'cdi-operator',
        file=cdi_operator_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider
        )
    )

    # Deploy the default CDI custom resource
    cdi_resource = CustomResource(
        "cdi",
        api_version="cdi.kubevirt.io/v1beta1",
        kind="CDI",
        metadata={
            "name": "cdi",
            "namespace": "cdi",
        },
        spec={
            "config": {
                "featureGates": [
                    "HonorWaitForFirstConsumer",
                ],
            },
            "imagePullPolicy": "IfNotPresent",
            "infra": {
                "nodeSelector": {
                    "kubernetes.io/os": "linux",
                },
                "tolerations": [
                    {
                        "key": "CriticalAddonsOnly",
                        "operator": "Exists",
                    },
                ],
            },
            "workload": {
                "nodeSelector": {
                    "kubernetes.io/os": "linux",
                },
            },
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[operator]
            #parent=namespace
        )
    )

    return version, operator
