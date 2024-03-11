import os
import pulumi
import pulumi_kubernetes as k8s

from src.kargo.cluster_network_addons.deploy import deploy_cluster_network_addons
from src.kargo.cilium.deploy import deploy_cilium
from src.kargo.kubevirt.deploy import deploy_kubevirt
from src.kargo.ceph.deploy import deploy_rook_operator
from src.kargo.cert_manager.deploy import deploy_cert_manager
from src.kargo.local_path_storage.deploy import deploy_local_path_storage
from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.lib.namespace import create_namespaces

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
    l2_bridge_name = "br0"
    l2announcements = "192.168.1.70/28"
    cilium_helm_release = deploy_cilium(
        "cilium-release",
        k8s_provider,
        kubernetes_distribution,
        "kargo",
        kubernetes_endpoint_ip.ips,
        "kube-system",
        l2_bridge_name,
        l2announcements
    )

    # Deploy KubeVirt
    kubevirt_version = deploy_kubevirt(
        k8s_provider,
        kubernetes_distribution
    )

    # Deploy Cluster Network Addons Operator
    # Enable multus with the following command:
    #   ~$ pulumi config set cnao.enabled true
    multus_enabled = config.get_bool('multus.enabled') or False
    if multus_enabled:
        # Deploy Multus
        multus = deploy_cluster_network_addons(k8s_provider)

    # check if local-path-provisioner pulumi config local_path_storage.enabled is set to true and deploy local-path-provisioner if it is
    # Enable local-path-provisioner with the following command:
    #   ~$ pulumi config set local_path_storage.enabled true
    # Configure local path default_path with the following command:
    #   ~$ pulumi config set local_path_storage.default_path /mnt/local-path-provisioner/dev/nvme0n1
    local_path_storage_enabled = config.get_bool('local_path_storage.enabled') or False
    if local_path_storage_enabled and not kubernetes_distribution == "kind":
        default_path = config.require('local_path_storage.default_path')
        # Deploy local-path-provisioner
        local_path_provisioner = deploy_local_path_storage(
            k8s_provider,
            "local-path-storage",
            default_path
        )
        #pulumi.export('local_path_provisioner', local_path_provisioner)

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
        pulumi.export('rook_operator', rook_operator)

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
        #pulumi.export('cert_manager', cert_manager)

    # Export deployment details
    #pulumi.export('helm_release_name', cilium_helm_release.resource_names)
    pulumi.export('k8s_provider', k8s_provider)
    #pulumi.export('namespace_names', [ns.metadata.name for ns in namespace_objects])
    pulumi.export('kubeconfig_context', kubeconfig_context)
    pulumi.export('kubernetes_distribution', kubernetes_distribution)
    #pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)
    #pulumi.export('kubevirt_version', kubevirt_version)

# Execute the main function
main()
