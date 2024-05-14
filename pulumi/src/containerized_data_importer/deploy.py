import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource
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
    operator = k8s.yaml.ConfigFile(
        'cdi-operator',
        file=cdi_operator_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    ## Deploy the default CDI custom resource
    #cdi_cr_url = f'https://github.com/kubevirt/containerized-data-importer/releases/download/v{version}/cdi-cr.yaml'
    #cdi_cr = k8s.yaml.ConfigFile(
    #    'cdi-cr',
    #    file=cdi_cr_url,
    #    opts=pulumi.ResourceOptions(
    #        provider=k8s_provider,
    #        #parent=namespace,
    #        depends_on=[operator]
    #    )
    #)

    return version, operator
