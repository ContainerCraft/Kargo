import pulumi
import pulumi_kubernetes as k8s
from src.kargo.cilium import deploy as deploy_cilium
from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.lib.namespace import create_namespaces
import os

def main():
    """
    Deploys the ContainerCraft Kargo Kubevirt Platform in Kubernetes using Pulumi.

    It initializes the Pulumi configuration, sets up the Kubernetes provider,
    creates namespaces, and deploys platform components.
    """

    # Initialize Pulumi configuration
    config = pulumi.Config()

    kubeconfig = os.getenv("KUBECONFIG")  or ".kube/config"
    kubeconfig_context = config.require('kubecontext')
    kubernetes_distribution = config.require('kubernetes')

    # Initialize the Kubernetes provider with the chosen context
    k8s_provider = k8s.Provider(
        "k8sProvider",
        context=kubeconfig_context,
        kubeconfig=kubeconfig,
        suppress_deprecation_warnings=True,
        suppress_helm_hook_warnings=True,
        enable_server_side_apply=True
    )

    # Get the Kubernetes API endpoint IP
    kubernetes_endpoint_ip = KubernetesApiEndpointIp("k8s-api-ip", k8s_provider)

    # Define desired namespaces in a list
    namespaces = ["kargo"]

    # Create namespaces
    namespace_objects = create_namespaces(namespaces, k8s_provider)

    # Deploy Cilium in the first namespace from the namespaces list
    cilium_helm_release = deploy_cilium(
        "cilium-release",
        k8s_provider,
        kubernetes_distribution,
        "kargo",
        kubernetes_endpoint_ip.ips,
        "kube-system"
    )

    pulumi.export('helm_release_name', cilium_helm_release.resource_names)
    pulumi.export('k8s_provider', k8s_provider)
    pulumi.export('namespace_names', [ns.metadata.name for ns in namespace_objects])
    pulumi.export('kubeconfig_context', kubeconfig_context)
    pulumi.export('kubernetes_distribution', kubernetes_distribution)
    pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)

# Execute the main function
main()
