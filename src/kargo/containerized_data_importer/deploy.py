import pulumi
import pulumi_kubernetes as k8s
import requests
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

def deploy_cdi(k8s_provider: k8s.Provider):
    """
    Fetches the latest stable version of CDI, deploys the CDI operator,
    and the default CDI custom resource using the fetched version.

    :param k8s_provider: A Pulumi Kubernetes provider.
    """

    # Fetch the latest stable version of CDI
    tag_url = 'https://github.com/kubevirt/containerized-data-importer/releases/latest'
    tag = requests.get(tag_url, allow_redirects=False).headers.get('location')
    cdi_version = tag.split('/')[-1] if tag else 'v1.58.2'  # Default to a known version if fetch fails

    # Deploy the CDI operator
    cdi_operator_url = f'https://github.com/kubevirt/containerized-data-importer/releases/download/{cdi_version}/cdi-operator.yaml'
    cdi_operator = k8s.yaml.ConfigFile(
        'cdi-operator',
        file=cdi_operator_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Deploy the default CDI custom resource
    cdi_cr_url = f'https://github.com/kubevirt/containerized-data-importer/releases/download/{cdi_version}/cdi-cr.yaml'
    cdi_cr = k8s.yaml.ConfigFile(
        'cdi-cr',
        file=cdi_cr_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Export the version of CDI that was deployed
    pulumi.export("cdi_version", cdi_version)
    cdi = {
        "operator": cdi_operator,
        "customResource": cdi_cr
    }
    return cdi
