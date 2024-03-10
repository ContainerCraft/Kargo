import pulumi
from pulumi import export as export
import pulumi_kubernetes as k8s
from src.kargo.cilium import deploy as deploy_cilium
from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.lib.namespace import create_namespaces
from src.kargo.kubevirt import deploy_kubevirt  # Import the KubeVirt deployment
from src.kargo.ceph.deploy import deploy as deploy_rook_operator  # Import the Rook Ceph deployment
from src.kargo.cert_manager.deploy import deploy as deploy_cert_manager  # Import the Rook Ceph deployment
import os

def main():
    """
    Deploys the ContainerCraft Kargo Kubevirt Platform in Kubernetes using Pulumi.
    """

    # Initialize Pulumi configuration
    config = pulumi.Config()

    kubeconfig = os.getenv("KUBECONFIG")  or ".kube/config"
    kubeconfig_context = config.require('kubecontext')
    kubernetes_distribution = config.require('kubernetes')

    # Initialize the Kubernetes provider
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

    # Define desired namespaces
    namespaces = [
        "kargo",
        "kubevirt",
        "rook-ceph"
    ]

    # Create namespaces
    namespace_objects = create_namespaces(namespaces, k8s_provider)

    # Deploy Cilium
    cilium_helm_release = deploy_cilium(
        "cilium-release",
        k8s_provider,
        kubernetes_distribution,
        "kargo",
        kubernetes_endpoint_ip.ips,
        "kube-system"
    )

    # Deploy KubeVirt
    kubevirt_version = deploy_kubevirt(
        k8s_provider,
        kubernetes_distribution
    )

    # check if pulumi config ceph.enabled is set to true and deploy rook-ceph if it is
    # Enable ceph operator with the following command:
    #   ~$ pulumi config set ceph.enabled true
    deploy_ceph = config.get_bool('ceph.enabled') or False
    if deploy_ceph:
        # Deploy Rook Ceph
        rook_operator = deploy_rook_operator(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "rook-ceph"
        )
        export('rook_operator', rook_operator)

    # Enable cert_manager witht the following command:
    #   ~$ pulumi config set cert_manager.enabled true
    cert_manager_enabled = config.get_bool('cert_manager.enabled') or False
    if cert_manager_enabled:
        # Deploy Cert Manager
        cert_manager = deploy_cert_manager(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "cert-manager"
        )
        export('cert_manager', cert_manager)

    # Export deployment details
    export('helm_release_name', cilium_helm_release.resource_names)
    export('k8s_provider', k8s_provider)
    export('namespace_names', [ns.metadata.name for ns in namespace_objects])
    export('kubeconfig_context', kubeconfig_context)
    export('kubernetes_distribution', kubernetes_distribution)
    export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)
    export('kubevirt_version', kubevirt_version)

# Execute the main function
main()
