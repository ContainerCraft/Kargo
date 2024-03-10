import pulumi
from pulumi_kubernetes import helm, Provider
from ...lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_rook_operator(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    """
    Deploy Ceph Operator using the Helm chart.

    Args:
        name (str): The name of the release.
        k8s_provider (Provider): The Kubernetes provider.
        kubernetes_distribution (str): The Kubernetes distribution.
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.
        namespace (str): The namespace to deploy Rook Ceph into.

    Returns:
        pulumi.helm.v3.Release: The deployed Rook Ceph Helm release.
    """
    # Determine Helm values based on the Kubernetes distribution
    helm_values = gen_helm_values(kubernetes_distribution, project_name)

    # Fetch the latest version from the helm chart index
    chart_url = "https://charts.rook.io/master/index.yaml"
    chart_name = "rook-ceph"
    chart_version = get_latest_helm_chart_version(chart_url, chart_name)

    # Deploy Rook Ceph Operator using the Helm chart
    release = helm.v3.Release(
        name,
        chart="rook-ceph",
        version=chart_version,
        #values=helm_values,
        values={},
        namespace=namespace,
        repository_opts={"repo": "https://charts.rook.io/release"},
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return(release, chart_version)

def gen_helm_values(kubernetes_distribution: str, project_name: str):
    """
    Get the Helm values for installing Rook Ceph based on the specified Kubernetes distribution.

    Args:
        kubernetes_distribution (str): The Kubernetes distribution (e.g., 'kind', 'talos').
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.

    Returns:
        dict: The Helm values for installing Rook Ceph.

    Raises:
        ValueError: If the specified Kubernetes distribution is not supported.
    """
    common_values = {
    }

    if kubernetes_distribution == 'kind':
        # Kind-specific Helm values
        return {
            **common_values,
            "csi": {
                "clusterName": project_name,
            },
            "logLevel": "INFO",
        }
    elif kubernetes_distribution == 'talos':
        # Talos-specific Helm values per the Talos Docs
        return {
            **common_values,
        }
    else:
        raise ValueError(f"Unsupported Kubernetes distribution: {kubernetes_distribution}")
