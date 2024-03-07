import pulumi
import pulumi_kubernetes as k8s
import requests

def deploy_kubevirt(k8s_provider: k8s.Provider):
    """
    Fetches the latest stable version of KubeVirt, and deploys the KubeVirt operator
    and custom resource using the fetched version.

    :param k8s_provider: A Pulumi Kubernetes provider.
    :return: The version of KubeVirt that was deployed.
    """

    # Fetch the latest stable version of KubeVirt
    kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
    kubevirt_version = requests.get(kubevirt_stable_version_url).text.strip()

    # Deploy the KubeVirt operator
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/{kubevirt_version}/kubevirt-operator.yaml'
    kubevirt_operator = k8s.yaml.ConfigFile(
        'kubevirt-operator',
        file=kubevirt_operator_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Deploy the KubeVirt Custom Resource
    kubevirt_cr_url = f'https://github.com/kubevirt/kubevirt/releases/download/{kubevirt_version}/kubevirt-cr.yaml'
    kubevirt_cr = k8s.yaml.ConfigFile(
        'kubevirt-cr',
        file=kubevirt_cr_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return kubevirt_version
