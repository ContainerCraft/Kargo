import os
import pulumi
import pulumi_kubernetes as k8s

from src.lib.namespace import create_namespaces
from src.kargo.multus.deploy import deploy_multus
from src.kargo.cilium.deploy import deploy_cilium
from src.kargo.kubevirt.deploy import deploy_kubevirt
from src.kargo.ceph.deploy import deploy_rook_operator
from src.kargo.openunison.deploy import deploy_openunison
from src.kargo.prometheus.deploy import deploy_prometheus
from src.kargo.cert_manager.deploy import deploy_cert_manager
from src.kargo.kv_manager.deploy import deploy_ui_for_kubevirt
from src.kargo.containerized_data_importer.deploy import deploy_cdi
from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.kargo.local_path_storage.deploy import deploy_local_path_storage
from src.kargo.hostpath_provisioner.deploy import deploy as deploy_hostpath_provisioner
from src.kargo.cluster_network_addons.deploy import deploy_cluster_network_addons as deploy_cnao

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

    # Default Cilium to disabled
    # Deploy Cilium
    l2_bridge_name = "br0"
    l2announcements = "192.168.1.70/28"
    enabled = config.get_bool('cilium.enabled') or False
    if enabled:
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

    # Enable cert_manager witht the following command:
    #   ~$ pulumi config set cert_manager.enabled true
    # Deploy Cert Manager
    cert_manager = deploy_cert_manager(
        "kargo",
        k8s_provider,
        kubernetes_distribution,
        "kargo",
        "cert-manager"
    )

    # Deploy KubeVirt
    kubevirt = deploy_kubevirt(
        k8s_provider,
        kubernetes_distribution,
        cert_manager
    )

    # Deploy CDI
    # Enable containerized data importer with the following command:
    #   ~$ pulumi config set cdi.enabled true
    if config.get_bool('cdi.enabled') or True:
        containerized_data_importer = deploy_cdi(
            k8s_provider
        )

    # Deploy Cluster Network Addons Operator
    # Enable multus with the following command:
    #   ~$ pulumi config set cnao.enabled true
    multus_enabled = config.get_bool('multus.enabled') or False
    if multus_enabled:
        # Deploy Cluster Network Addons Operator
        cnao = deploy_cnao(k8s_provider)
        # Deploy Multus
        multus = deploy_multus(k8s_provider)

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

    # check if hostpath-provisioner pulumi config hostpath_provisioner.enabled is set to true and deploy if it is
    # Enable hostpath-provisioner with the following command:
    #   ~$ pulumi config set hostpath_provisioner.enabled true
    # configure hostpath-provisioner default storage path with the following command:
    #   ~$ pulumi config set hostpath_provisioner.default_path /var/mnt/block/dev/sda
    # Set hostpath-provisioner version override with the following command:
    #   ~$ pulumi config set hostpath_provisioner.version v0.17.0
    # Configure hostpath-provisioner to be the default storage class with the following command:
    #   ~$ pulumi config set hostpath_provisioner.default_storage_class true
    hostpath_provisioner_enabled = config.get_bool('hostpath_provisioner.enabled') or False
    hostpath_version = config.get('hostpath_provisioner.version') or None
    hostpath_default_path = config.get('hostpath_provisioner.default_path') or "/var/mnt"
    hostpath_default_storage_class = config.get('hostpath_provisioner.default_storage_class') or "false"
    if hostpath_provisioner_enabled:
        # Deploy hostpath-provisioner
        hostpath_provisioner = deploy_hostpath_provisioner(
            k8s_provider,
            hostpath_default_path,
            hostpath_default_storage_class,
            hostpath_version,
            cert_manager
        )

    # check if pulumi config openunison.enabled is set to true and deploy openunison if it is
    openunison_enabled = config.get_bool('openunison.enabled') or False
    if openunison_enabled:
        # Deploy OpenUnison
        openunison = deploy_openunison(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "openunison"
        )
        pulumi.export('openunison', openunison)

    # check if pulumi config prometheus.enabled is set to true and deploy prometheus if it is
    prometheus_enabled = config.get_bool('prometheus.enabled') or False
    if prometheus_enabled:
        # Deploy prometheus
        prometheus = deploy_prometheus(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "prometheus"
        )
        pulumi.export('prometheus', prometheus)

    # check if pulumi config kubevirt_manager.enabled is set to true and deploy kubervirt-manager if it is
    kubevirt_manager_enabled = config.get_bool('kubevirt_manager.enabled') or False
    if kubevirt_manager_enabled:
        # Deploy kubevirt-manager
        kubevirt_manager = deploy_ui_for_kubevirt(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "kubevirt_manager"
        )
        pulumi.export('kubervirt_manager', kubevirt_manager)

    # Export deployment details
    #pulumi.export('helm_release_name', cilium_helm_release.resource_names)
    pulumi.export('k8s_provider', k8s_provider)
    #pulumi.export('namespace_names', [ns.metadata.name for ns in namespace_objects])
    pulumi.export('kubeconfig_context', kubeconfig_context)
    pulumi.export('kubernetes_distribution', kubernetes_distribution)
    #pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)
    #pulumi.export('kubevirt', kubevirt)

# Execute the main function
main()
