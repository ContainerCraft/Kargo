import pulumi
from pulumi_kubernetes import helm, Provider
from typing import Optional
from ..lib.helm_chart_versions import get_latest_helm_chart_version

def deploy(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, kubernetes_endpoint_ip_string: str, namespace: str):
    """
    Deploy Cilium using the Helm chart.

    Args:
        name (str): The name of the release.
        k8s_provider (Provider): The Kubernetes provider.
        kubernetes_distribution (str): The Kubernetes distribution.
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.
        namespace (str): The namespace to deploy Cilium to.

    Returns:
        pulumi.helm.v3.Release: The deployed Cilium Helm release.
    """
    # Determine Helm values based on the Kubernetes distribution
    helm_values = get_helm_values(kubernetes_distribution, project_name, kubernetes_endpoint_ip_string)

    # Fetch the latest version of the Cilium Helm chart
    cilium_chart_url = "https://raw.githubusercontent.com/cilium/charts/master/index.yaml"
    cilium_chart_name = "cilium"
    cilium_latest_version = get_latest_helm_chart_version(cilium_chart_url, cilium_chart_name)

    # Statically limit the Cilium version to 1.14.5 until
    cilium_latest_version = "1.14.5"

    # Deploy Cilium using the Helm chart
    return helm.v3.Release(
        name,
        chart="cilium",
        version=cilium_latest_version,
        values=helm_values,
        namespace=namespace,
        repository_opts={"repo": "https://helm.cilium.io/"},
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

def get_helm_values(kubernetes_distribution: str, project_name: str, kubernetes_endpoint_ip_string: str):
    """
    Get the Helm values for installing Cilium based on the specified Kubernetes distribution.

    Args:
        kubernetes_distribution (str): The Kubernetes distribution (e.g., 'kind', 'talos').
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.

    Returns:
        dict: The Helm values for installing Cilium.

    Raises:
        ValueError: If the specified Kubernetes distribution is not supported.
    """
    common_values = {
        "cluster": {"name": project_name},
        "ipam": {"mode": "kubernetes"},
        "serviceAccounts": {
            "cilium": {"name": "cilium"},
            "operator": {"name": "cilium-operator"},
        },
    }

    if kubernetes_distribution == 'kind':
        return {
            **common_values,
            "k8sServiceHost": kubernetes_endpoint_ip_string,
            "k8sServicePort": 6443,
            "kubeProxyReplacement": "strict",
            "operator": {"replicas": 1},
            "routingMode": "tunnel",
        }
    elif kubernetes_distribution == 'talos':
        # Talos-specific Helm values per the Talos Cilium Docs
        return {
            **common_values,
            "cgroup": {
                "autoMount": {"enabled": False},
                "hostRoot": "/sys/fs/cgroup",
            },
            "routingMode": "tunnel",
            "k8sServicePort": 7445,
            "tunnelProtocol": "vxlan",
            "k8sServiceHost": "localhost",
            "kubeProxyReplacement": "strict",
            "image": {"pullPolicy": "IfNotPresent"},
            "hostServices": {"enabled": False},
            "externalIPs": {"enabled": True},
            "gatewayAPI": {"enabled": True},
            "nodePort": {"enabled": True},
            "hostPort": {"enabled": True},
            "operator": {"replicas": 1},
            "cni": { "install": True},
            "securityContext": {
                "capabilities": {
                    "ciliumAgent": [
                        "CHOWN", "KILL", "NET_ADMIN", "NET_RAW", "IPC_LOCK",
                        "SYS_ADMIN", "SYS_RESOURCE", "DAC_OVERRIDE", "FOWNER",
                        "SETGID", "SETUID"
                    ],
                    "cleanCiliumState": ["NET_ADMIN", "SYS_ADMIN", "SYS_RESOURCE"],
                },
            },
        }
    else:
        raise ValueError(f"Unsupported Kubernetes distribution: {kubernetes_distribution}")
