import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider

from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.cilium.deploy import deploy_cilium
from src.cert_manager.deploy import deploy_cert_manager
from src.kubevirt.deploy import deploy_kubevirt
from src.containerized_data_importer.deploy import deploy_cdi
from src.cluster_network_addons.deploy import deploy_cnao
from src.multus.deploy import deploy_multus
from src.hostpath_provisioner.deploy import deploy as deploy_hostpath_provisioner
from src.openunison.deploy import deploy_openunison
from src.prometheus.deploy import deploy_prometheus
from src.kubernetes_dashboard.deploy import deploy_kubernetes_dashboard
#from src.kv_manager.deploy import deploy_ui_for_kubevirt
#from src.ceph.deploy import deploy_rook_operator

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

versions = {}

##################################################################################
## Enable/Disable Kargo Kubevirt PaaS Infrastructure Modules
##################################################################################

# Disable Cilium with the following command:
#   ~$ pulumi config set cilium.enable false
cilium_enabled = config.get_bool('cilium.enabled') or False

# Enable cert-manager with the following command:
#   ~$ pulumi config set cert_manager.enable true
cert_manager_enabled = config.get_bool('cert_manager.enabled') or True

# Enable KubeVirt with the following command:
#   ~$ pulumi config set kubevirt.enable true
kubevirt_enabled = config.get_bool('kubevirt.enabled') or True

# Enable containerized data importer with the following command:
#   ~$ pulumi config set cdi.enabled true
cdi_enabled = config.get_bool('cdi.enabled') or False

# Set Multus version override with the following command:
#   ~$ pulumi config set multus.version 3.7.0
multus_enabled = config.get_bool('multus.enabled') or False

# Set prometheus enabled with the following command:
#   ~$ pulumi config set prometheus.enabled true
prometheus_enabled = config.get_bool('prometheus.enabled') or False

# Set openunison enabled with the following command:
#   ~$ pulumi config set openunison.enabled true
openunison_enabled = config.get_bool('openunison.enabled') or False

# Configure hostpath-provisioner to be the default storage class with the following command:
#   ~$ pulumi config set hostpath_provisioner.default_storage_class true
hostpath_provisioner_enabled = config.get_bool('hostpath_provisioner.enabled') or False

# Configure CNAO to be enabled with the following command:
#  ~$ pulumi config set cnao.enabled true
cnao_enabled = config.get_bool('cnao.enabled') or False

# Configure Kubernetes Dashboard enabled with the following command:
#   ~$ pulumi config set kubernetes_dashboard.enabled true
kubernetes_dashboard_enabled = config.get_bool("kubernetes_dashboard.enabled") or False

# Configure Kubevirt Manager GUI enabled with the following command:
#   ~$ pulumi config set kubevirt_manager.enabled true
kubevirt_manager_enabled = config.get_bool("kubevirt_manager.enabled") or False

##################################################################################
## Get the Kubernetes API endpoint IP
##################################################################################

# Get the Kubernetes API endpoint IP
k8s_endpoint_ip = KubernetesApiEndpointIp(
    "kubernetes-endpoint-service-address",
    k8s_provider
)

# Extract the Kubernetes Endpoint clusterIP
kubernetes_endpoint_service = pulumi.Output.from_input(k8s_endpoint_ip)
kubernetes_endpoint_service_address = kubernetes_endpoint_service.endpoint.subsets[0].addresses[0].ip
pulumi.export(
    "kubernetes-endpoint-service-address",
    kubernetes_endpoint_service_address
)

##################################################################################
## Core Kargo Kubevirt PaaS Infrastructure
##################################################################################

##################################################################################
# Deploy Cilium CNI
if cilium_enabled:
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

    # Append cilium version to versions dictionary
    versions["cilium"] = {"enabled": cilium_enabled, "version": cilium[0]}

    # Cilium Release Resource
    cilium_release = cilium[1]

else:
    # Set version and release resource objects to None if Cilium is disabled
    cilium = None, None

##################################################################################
# Deploy Cert Manager
if cert_manager_enabled:

    # Cert Manager namespace
    ns_name = "cert-manager"

    # Set cert-manager version override with the following command:
    #   ~$ pulumi config set cert_manager.version v1.5.3
    version = config.get('cert_manager.version') or None

    # Set depends to an empty list by default
    depends = []

    # Set cilium as a dependency for cert-manager
    if cilium_enabled:
        depends.append(cilium_release)

    # Deploy Cert Manager
    cert_manager = deploy_cert_manager(
        ns_name,
        version,
        kubernetes_distribution,
        depends,
        k8s_provider
    )

    # Append cert-manager version to versions dictionary
    versions["cert_manager"] = {"enabled": cert_manager_enabled, "version": cert_manager[0]}

    # Cert Manager Release Resource
    cert_manager_release = cert_manager[1]

    cert_manager_selfsigned_cert = cert_manager[2]

    pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)

else:
    cert_manager = None, None

##################################################################################
# Deploy KubeVirt
if kubevirt_enabled:

    # Check for Kubevirt version override
    # Set kubevirt version override with the following command:
    #   ~$ pulumi config set kubevirt.version v0.45.0
    version = config.get('kubevirt.version') or None

    # Set depends to an empty list by default
    depends = []

    # Set cert-manager as a dependency of KubeVirt
    if cert_manager_enabled:
        depends.append(cert_manager_release)

    # KubeVirt namespace
    ns_name = "kubevirt"

    # Deploy KubeVirt
    kubevirt = deploy_kubevirt(
        depends,
        ns_name,
        version,
        k8s_provider,
        kubernetes_distribution,
    )

    # Append kubevirt version to versions dictionary
    versions["kubevirt"] = {"enabled": kubevirt_enabled, "version": kubevirt[0]}

    # KubeVirt Release Resource
    kubevirt_operator = kubevirt[1]

else:
    kubevirt = None, None

##################################################################################
# Deploy Containerized Data Importer (CDI)
if cdi_enabled:

    # Set CDI version override from Pulumi config
    # Set version override with the following command:
    #   ~$ pulumi config set cdi.version v1.14.7
    version = config.get('cdi.version') or None

    # Set depends to an empty list by default
    depends = []

    # Set Kubevirt as a dependency for CDI
    if kubevirt_enabled:
        depends.append(kubevirt_operator)

    containerized_data_importer = deploy_cdi(
        depends,
        version,
        k8s_provider
    )

    # Append CDI version to versions dictionary
    versions["cdi"] = {"enabled": cdi_enabled, "version": containerized_data_importer[0]}

    # CDI Release Resource
    cdi_release = containerized_data_importer[1]

else:
    containerized_data_importer = None, None

##################################################################################
# Deploy Cluster Network Addons Operator (CNAO)
if cnao_enabled:

    # Set CNAO version override from Pulumi config
    #   ~$ pulumi config set cnao.version 1.14.7
    version_cnao = config.get('cnao.version') or None

    # Set depends to an empty list by default
    depends = []

    # Set Cilium as a dependency for CNAO
    if cilium_enabled:
        depends.append(cilium_release)

    # Deploy Cluster Network Addons Operator
    cnao = deploy_cnao(
        depends,
        version_cnao,
        k8s_provider
    )

    # Append CNAO version to versions dictionary
    versions["cnao"] = {"enabled": cnao_enabled, "version": cnao[0]}

    # CNAO Release Resource
    cnao_release = cnao[1]

else:
    cnao = None, None

##################################################################################
# Deploy Multus
if multus_enabled:

    # Set Multus version override from Pulumi config
    version = config.get('multus.version') or "master"

    # Set depends to an empty list by default
    depends = []

    # Set Cilium as a dependency for Multus
    if cilium_enabled:
        depends.append(cilium_release)

    # Set Multus default bridge name with the following command:
    #   ~$ pulumi config set multus.default_bridge br0
    bridge_name = config.get('multus.default_bridge') or "br0"

    # Deploy Multus
    multus = deploy_multus(
        depends,
        version,
        bridge_name,
        k8s_provider
    )

    # Append Multus version to versions dictionary
    versions["multus"] = {"enabled": multus_enabled, "version": multus[0]}

    # Multus Release Resource
    multus_release = multus[1]

else:
    multus = None, None

##################################################################################
# Deploy Hostpath Provisioner
if hostpath_provisioner_enabled:

    # Set Version of hostpath-provisioner
    version = config.get('hostpath_provisioner.version') or None

    # configure hostpath-provisioner default storage path with the following command:
    #   ~$ pulumi config set hostpath_provisioner.default_path /var/mnt/block/dev/sda
    # Set hostpath-provisioner version override with the following command:
    #   ~$ pulumi config set hostpath_provisioner.version v0.17.0
    hostpath_default_path = config.get('hostpath_provisioner.default_path') or "/var/mnt"
    hostpath_default_storage_class = config.get('hostpath_provisioner.default_storage_class') or False

    # Set hostpath-provisioner namespace
    ns_name = "hostpath-provisioner"

    # set depends to an empty list by default
    depends = []

    # Add dependencies to the depends list
    if cilium_enabled:
        depends.append(cilium_release)

    if cert_manager:
        depends.append(cert_manager_release)

    # Deploy hostpath-provisioner
    hostpath_provisioner = deploy_hostpath_provisioner(
        depends,
        version,
        ns_name,
        hostpath_default_path,
        hostpath_default_storage_class,
        k8s_provider,
    )

    # Append hostpath-provisioner version to versions dictionary
    versions["hostpath_provisioner"] = {"enabled": hostpath_provisioner_enabled, "version": hostpath_provisioner[0]}

    # Hostpath Provisioner Release Resource
    hostpath_provisioner_release = hostpath_provisioner[1]

else:
    hostpath_provisioner = None, None

##################################################################################
# Deploy Prometheus
if prometheus_enabled:

    # Set prometheus version override with the following command:
    #   ~$ pulumi config set prometheus.version v0.45.0
    version = config.get('prometheus.version') or None

    # Set prometheus namespace
    ns_name = "monitoring"

    # Set depends to an empty list by default
    depends = []

    # Append cilium_release to depends if cilium_enabled is true
    if cilium_enabled:
        depends.append(cilium_release)

    # Deploy prometheus
    prometheus = deploy_prometheus(
        depends,
        ns_name,
        version,
        k8s_provider,
        openunison_enabled
    )

    # Append prometheus version to versions dictionary
    versions["prometheus"] = {"enabled": prometheus_enabled, "version": prometheus[0]}

    # Prometheus Release Resource
    prometheus_release = prometheus[1]

else:
    prometheus = None, None

##################################################################################
# Deploy Kubernetes Dashboard
if kubernetes_dashboard_enabled:

    # Set version override with the following command:
    #   ~$ pulumi config set kubernetes_dashboard.version 1.0.0
    version = config.get('kubernetes_dashboard.version') or None

    # Set depends to an empty list by default
    depends = []

    # Append cilium_release to depends if cilium_enabled is true
    if cilium_enabled:
        depends.append(cilium_release)

    # Set openunison namespace
    ns_name = "kubernetes-dashboard"

    # Deploy OpenUnison
    kubernetes_dashboard = deploy_kubernetes_dashboard(
        depends,
        ns_name,
        version,
        k8s_provider
    )

    # Append kubernetes_dashboard version to versions dictionary
    versions["kubernetes_dashboard"] = {"enabled": kubernetes_dashboard_enabled, "version": kubernetes_dashboard[0]}

    # Kubernetes Dashboard Release
    kubernetes_dashboard_release = kubernetes_dashboard[1]

else:
    kubernetes_dashboard = None, None

##################################################################################
# Deploy OpenUnison
if openunison_enabled:

    # Set openunison version override with the following command:
    #   ~$ pulumi config set openunison.version v1.0.0
    version = config.get('openunison.version') or None

    # get the domain suffix and cluster_issuer
    domain_suffix = config.get('openunison.dns_suffix') or "kargo.arpa"

    # get the cluster issuer
    cluster_issuer = config.get('openunison.cluster_issuer') or "cluster-selfsigned-issuer-ca"

    # Set openunison github integration config values
    openunison_github_teams = config.require('openunison.github.teams')
    openunison_github_client_id = config.require('openunison.github.client_id')
    openunison_github_client_secret = config.require('openunison.github.client_secret')

    # Set depends to an empty list by default
    depends = []

    # Append cilium_release to depends if cilium_enabled is true
    if cilium_enabled:
        depends.append(cilium_release)

    # Append cert_manager_release to depends if cert_manager is enabled
    if cert_manager_enabled:
        depends.append(cert_manager_release)

    # Append prometheus_release to depends if prometheus_enabled is true
    if prometheus_enabled:
        depends.append(prometheus_release)

    enabled = {}

    if kubevirt_enabled:
        enabled["kubevirt"] = {"enabled": kubevirt_enabled}

    if prometheus_enabled:
        enabled["prometheus"] = {"enabled": prometheus_enabled}

    pulumi.export("enabled", enabled)

    # Set openunison namespace
    ns_name = "openunison"

    # Deploy OpenUnison
    openunison = deploy_openunison(
        depends,
        ns_name,
        version,
        k8s_provider,
        domain_suffix,
        cluster_issuer,
        cert_manager_selfsigned_cert,
        kubernetes_dashboard_release,
        openunison_github_client_id,
        openunison_github_client_secret,
        openunison_github_teams,
        enabled,
    )

    # Append openunison version to versions dictionary
    #versions["openunison"] = {"enabled": openunison_enabled, "version": openunison[0]}

    # OpenUnison Release Resource
    #openunison_release = openunison[1]

else:
    openunison = None, None

# Export the component versions
pulumi.export("versions", versions)

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
