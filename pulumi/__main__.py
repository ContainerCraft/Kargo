import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider

from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.cilium.deploy import deploy_cilium
from src.cert_manager.deploy import deploy_cert_manager
from src.kubevirt.deploy import deploy_kubevirt
from src.containerized_data_importer.deploy import deploy_cdi
from src.cluster_network_addons.deploy import deploy_cnao
#from src.multus.deploy import deploy_multus
#from src.ceph.deploy import deploy_rook_operator
#from src.openunison.deploy import deploy_openunison
#from src.prometheus.deploy import deploy_prometheus
#from src.kv_manager.deploy import deploy_ui_for_kubevirt
#from src.local_path_storage.deploy import deploy_local_path_storage
#from src.hostpath_provisioner.deploy import deploy as deploy_hostpath_provisioner

##################################################################################
# Load the Pulumi Config
config = pulumi.Config()

# Get pulumi stack name
stack_name = pulumi.get_stack()

# Get the pulumi project name
project_name = pulumi.get_project()

# Get the kubeconfig file path from priority order:
#   1. Pulumi configuration value: `pulumi config set kubeconfig <path>`
kubernetes_config_filepath = config.require("kubeconfig")

# Get kubeconfig context from Pulumi config or default to "kind-pulumi"
kubernetes_context = config.get("kubeconfig.context") or "kind-kargo"

# Get the Kubernetes distribution from the Pulumi configuration or default to "kind"
kubernetes_distribution = config.get("kubernetes_distribution") or "kind"

# Create a Kubernetes provider instance
k8s_provider = Provider(
    "k8sProvider",
    kubeconfig=kubernetes_config_filepath,
    context=kubernetes_context
)

# Get the Kubernetes API endpoint IP
k8s_endpoint_ip = KubernetesApiEndpointIp(
    "kubernetes-endpoint-service-address",
    k8s_provider
)

# Extract the Kubernetes Endpoint clusterIP
kubernetes_endpoint_service_address = pulumi.Output.from_input(k8s_endpoint_ip)
pulumi.export(
    "kubernetes-endpoint-service-address",
    kubernetes_endpoint_service_address.endpoint.subsets[0].addresses[0].ip
)

##################################################################################
## Core Kargo Kubevirt PaaS Infrastructure
##################################################################################

# Cilium CNI
# Default Cilium to disabled
# Check pulumi config 'cilium.enable' and deploy if true
# Disable Cilium with the following command:
#   ~$ pulumi config set cilium.enable false
enable = config.get_bool('cilium.enable') or False
if enable:
    # Get Cilium configuration from Pulumi stack config
    # Set Cilium version override with the following command:
    #   ~$ pulumi config set cilium.version v1.14.7
    # TODO: fix hardcode limit Cilium version to 1.14.7 until upgrade to 15.x is resolved
    version = config.get('cilium.version') or "1.14.7"
    namespace = "kube-system"
    l2announcements = "192.168.1.70/28"
    l2_bridge_name = "br0"

    # Deploy Cilium
    cilium = deploy_cilium(
        "cilium-cni",
        k8s_provider,
        kubernetes_distribution,
        project_name,
        kubernetes_endpoint_service_address,
        namespace,
        version,
        l2_bridge_name,
        l2announcements
    )
    cilium_version = cilium[0]
    cilium_release = cilium[1]
else:
    # Set version and release resource objects to None if Cilium is disabled
    cilium = (None, None)

# Cert Manager
# Check pulumi config 'cert_manager.enable' and deploy if true
# Enable cert-manager with the following command:
#   ~$ pulumi config set cert_manager.enable true
enable = config.get_bool('cert_manager.enable') or True
if enable:

    # Set cert-manager version override with the following command:
    #   ~$ pulumi config set cert_manager.version v1.5.3
    version = config.get('cert_manager.version') or None

    # Cert Manager namespace
    ns_name = "cert-manager"

    # Deploy Cert Manager
    cert_manager = deploy_cert_manager(
        ns_name,
        version,
        kubernetes_distribution,
        k8s_provider
    )
    cert_manager_version = cert_manager[0]
    cert_manager_release = cert_manager[1]
else:
    # Set version and release objects to None if cert-manager is disabled
    cert_manager = None, None

# Deploy KubeVirt
# Check pulumi config 'kubevirt.enable' and deploy if true
# Enable KubeVirt with the following command:
#   ~$ pulumi config set kubevirt.enable true
enable = config.get_bool('kubevirt.enable') or True
if enable:

    # Check for Kubevirt version override
    # Set kubevirt version override with the following command:
    #   ~$ pulumi config set kubevirt.version v0.45.0
    version = config.get('kubevirt.version') or None

    # KubeVirt namespace
    ns_name = "kubevirt"

    # Deploy KubeVirt
    kubevirt = deploy_kubevirt(
        ns_name,
        version,
        k8s_provider,
        kubernetes_distribution,
        cert_manager_release
    )
    kubevirt_version = kubevirt[0]
    kubevirt_operator = kubevirt[1]
else:
    # Set kubevirt object to None if Kubevirt is disabled
    kubevirt = None, None

# Deploy CDI
# Enable containerized data importer with the following command:
#   ~$ pulumi config set cdi.enabled true
# Set version override with the following command:
#   ~$ pulumi config set cdi.version v1.14.7
version = config.get('cdi.version') or None
if config.get_bool('cdi.enabled') or True:
    containerized_data_importer = deploy_cdi(
        version,
        k8s_provider
    )

# Deploy Cluster Network Addons Operator
# Enable Cluster Network Addons Operator with the following command:
#   ~$ pulumi config set cnao.enabled true
# Set CNAO version override with the following command:
#   ~$ pulumi config set cnao.version 0.0.1
cnao_enabled = config.get_bool('cnao.enabled') or False
if cnao_enabled:

    # Set CNAO version override from Pulumi config
    version_cnao = config.get('cnao.version') or None

    # Deploy Cluster Network Addons Operator
    cnao = deploy_cnao(
        version_cnao,
        k8s_provider
    )

# Enable multus with the following command:
#   ~$ pulumi config set cnao.enabled true
# Set Multus version override with the following command:
#   ~$ pulumi config set multus.version 3.7.0
#multus_enabled = config.get_bool('multus.enabled') or False
#if multus_enabled:
    # Deploy Multus
    #multus = deploy_multus(k8s_provider)

## check if local-path-provisioner pulumi config local_path_storage.enabled is set to true and deploy local-path-provisioner if it is
## Enable local-path-provisioner with the following command:
##   ~$ pulumi config set local_path_storage.enabled true
## Configure local path default_path with the following command:
##   ~$ pulumi config set local_path_storage.default_path /mnt/local-path-provisioner/dev/nvme0n1
#local_path_storage_enabled = config.get_bool('local_path_storage.enabled') or False
#if local_path_storage_enabled and not kubernetes_distribution == "kind":
#    default_path = config.require('local_path_storage.default_path')
#    # Deploy local-path-provisioner
#    local_path_provisioner = deploy_local_path_storage(
#        k8s_provider,
#        "local-path-storage",
#        default_path
#    )
#
## check if pulumi config ceph.enabled is set to true and deploy rook-ceph if it is
## Enable ceph operator with the following command:
##   ~$ pulumi config set ceph.enabled true
#deploy_ceph = config.get_bool('ceph.enabled') or False
#if deploy_ceph:
#    # Deploy Rook Ceph
#    rook_operator = deploy_rook_operator(
#        "kargo",
#        k8s_provider,
#        kubernetes_distribution,
#        "kargo",
#        "rook-ceph"
#    )
#
## check if hostpath-provisioner pulumi config hostpath_provisioner.enabled is set to true and deploy if it is
## Enable hostpath-provisioner with the following command:
##   ~$ pulumi config set hostpath_provisioner.enabled true
## configure hostpath-provisioner default storage path with the following command:
##   ~$ pulumi config set hostpath_provisioner.default_path /var/mnt/block/dev/sda
## Set hostpath-provisioner version override with the following command:
##   ~$ pulumi config set hostpath_provisioner.version v0.17.0
## Configure hostpath-provisioner to be the default storage class with the following command:
##   ~$ pulumi config set hostpath_provisioner.default_storage_class true
#hostpath_provisioner_enabled = config.get_bool('hostpath_provisioner.enabled') or False
#hostpath_version = config.get('hostpath_provisioner.version') or None
#hostpath_default_path = config.get('hostpath_provisioner.default_path') or "/var/mnt/block/dev/sda"
#hostpath_default_storage_class = config.get('hostpath_provisioner.default_storage_class') or "false"
#if hostpath_provisioner_enabled:
#    # Deploy hostpath-provisioner
#    hostpath_provisioner = deploy_hostpath_provisioner(
#        k8s_provider,
#        hostpath_default_path,
#        hostpath_default_storage_class,
#        hostpath_version,
#        cert_manager
#    )
#
## check if pulumi config openunison.enabled is set to true and deploy openunison if it is
#openunison_enabled = config.get_bool('openunison.enabled') or False
#if openunison_enabled:
#    # Deploy OpenUnison
#    openunison = deploy_openunison(
#        "kargo",
#        k8s_provider,
#        kubernetes_distribution,
#        "kargo",
#        "openunison"
#    )
#    pulumi.export('openunison', openunison)
#
## check if pulumi config prometheus.enabled is set to true and deploy prometheus if it is
#prometheus_enabled = config.get_bool('prometheus.enabled') or False
#if prometheus_enabled:
#    # Deploy prometheus
#    prometheus = deploy_prometheus(
#        "kargo",
#        k8s_provider,
#        kubernetes_distribution,
#        "kargo",
#        "prometheus"
#    )
#    pulumi.export('prometheus', prometheus)
#
## check if pulumi config kubevirt_manager.enabled is set to true and deploy kubervirt-manager if it is
#kubevirt_manager_enabled = config.get_bool('kubevirt_manager.enabled') or False
#if kubevirt_manager_enabled:
#    # Deploy kubevirt-manager
#    kubevirt_manager = deploy_ui_for_kubevirt(
#        "kargo",
#        k8s_provider,
#        kubernetes_distribution,
#        "kargo",
#        "kubevirt_manager"
#    )
#    pulumi.export('kubervirt_manager', kubevirt_manager)
#
## Export deployment details
##pulumi.export('helm_release_name', cilium_helm_release.resource_names)
#pulumi.export('k8s_provider', k8s_provider)
##pulumi.export('namespace_names', [ns.metadata.name for ns in namespace_objects])
#pulumi.export('kubeconfig_context', kubeconfig_context)
#pulumi.export('kubernetes_distribution', kubernetes_distribution)
##pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)
##pulumi.export('kubevirt', kubevirt)
