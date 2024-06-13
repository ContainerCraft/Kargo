import os
import requests
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
from src.kv_manager.deploy import deploy_ui_for_kubevirt
from src.ceph.deploy import deploy_rook_operator

##################################################################################
# Load the Pulumi Config
config = pulumi.Config()

# Get pulumi stack name
stack_name = pulumi.get_stack()

# Get the pulumi project name
project_name = pulumi.get_project()

# Get the kubeconfig file path from priority order:
# Acquire kubeconfig file path from the following sources in order of priority:
#   1. Environment variable: `KUBECONFIG`
#   2. Pulumi configuration value: `pulumi config set kubeconfig <path>`

# Assemble the kubeconfig file path from cwd + KUBECONFIG
kubernetes_config_filepath = config.require("kubernetes.kubeconfig")

# Get kubeconfig context from Pulumi config or default to "kind-pulumi"
kubernetes_context = config.get("kubernetes.context") or "kind-kargo"

# Get the Kubernetes distribution from the Pulumi configuration or default to "kind"
kubernetes_distribution = config.get("kubernetes.distribution") or "kind"

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
cert_manager_enabled = config.get_bool('cert_manager.enabled') or False

# Enable KubeVirt with the following command:
#   ~$ pulumi config set kubevirt.enable true
kubevirt_enabled = config.get_bool('kubevirt.enabled') or False

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

# check if kubernetes distribution is "kind" and if so execute get the kubernetes api endpoint ip
if kubernetes_distribution == "kind":
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
else:
    # default to talos k8s endpoint "localhost" when not kind k8s
    kubernetes_endpoint_service_address = "localhost"

##################################################################################
## Core Kargo Kubevirt PaaS Infrastructure
##################################################################################

depends = []

##################################################################################
# Fetch the Cilium Version
# Deploy Cilium
def run_cilium():
    if cilium_enabled:
        namespace = "kube-system"
        l2announcements = "192.168.1.70/28"
        l2_bridge_name = "br0"
        cilium_version = config.get('cilium.version') # or "1.14.7"

        cilium = deploy_cilium(
            "cilium-cni",
            k8s_provider,
            kubernetes_distribution,
            project_name,
            kubernetes_endpoint_service_address,
            namespace,
            cilium_version,
            l2_bridge_name,
            l2announcements,
        )
        cilium_version = cilium[0]
        cilium_release = cilium[1]

        # Append cilium release to depends list
        depends.append(cilium_release)

        return cilium_version, cilium_release
    return None, None

cilium_version, cilium_release = run_cilium()

versions["cilium"] = {"enabled": cilium_enabled, "version": cilium_version}

##################################################################################
# Fetch the Cert Manager Version
# Deploy Cert Manager
def run_cert_manager():
    if cert_manager_enabled:
        ns_name = "cert-manager"
        cert_manager_version = config.get('cert_manager.version') or None

        cert_manager = deploy_cert_manager(
            ns_name,
            cert_manager_version,
            kubernetes_distribution,
            depends,
            k8s_provider
        )

        versions["cert_manager"] = {"enabled": cert_manager_enabled, "version": cert_manager[0]}
        cert_manager_release = cert_manager[1]
        cert_manager_selfsigned_cert = cert_manager[2]

        pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)

        # Append cert manager release to depends list
        depends.append(cert_manager[1])

        return cert_manager, cert_manager_release, cert_manager_selfsigned_cert
    return None, None, None

cert_manager, cert_manager_release, cert_manager_selfsigned_cert = run_cert_manager()

##################################################################################
# Deploy KubeVirt
def run_kubevirt():
    if kubevirt_enabled:
        ns_name = "kubevirt"
        kubevirt_version = config.get('kubevirt.version') or None

        custom_depends = []
        custom_depends.append(cilium_release)
        custom_depends.append(cert_manager_release)

        kubevirt = deploy_kubevirt(
            custom_depends,
            ns_name,
            kubevirt_version,
            k8s_provider,
            kubernetes_distribution,
        )

        versions["kubevirt"] = {"enabled": kubevirt_enabled, "version": kubevirt[0]}
        kubevirt_operator = kubevirt[1]

        # Append kubevirt version to versions dictionary
        depends.append(kubevirt_operator)

        return kubevirt, kubevirt_operator
    return None, None

kubevirt, kubevirt_operator = run_kubevirt()

##################################################################################
# Deploy Multus
def run_multus():
    if multus_enabled:
        ns_name = "multus"
        multus_version = config.get('multus.version') or "master"
        bridge_name = config.get('multus.default_bridge') or "br0"

        custom_depends = []

        if cilium_enabled:
            custom_depends.append(cilium_release)
        if cert_manager_enabled:
            custom_depends.append(cert_manager_release)

        multus = deploy_multus(
            custom_depends,
            multus_version,
            bridge_name,
            k8s_provider
        )

        versions["multus"] = {"enabled": multus_enabled, "version": multus[0]}
        multus_release = multus[1]

        # Append multus version to versions dictionary
        depends.append(multus_release)

        return multus, multus_release
    return None, None

multus, multus_release = run_multus()

##################################################################################
# Deploy Cluster Network Addons Operator (CNAO)
def run_cnao():
    if cnao_enabled:
        ns_name = "cluster-network-addons"
        cnao_version = config.get('cnao.version') or None

        custom_depends = []

        if cilium_enabled:
            custom_depends.append(cilium_release)

        if cert_manager_enabled:
            custom_depends.append(cert_manager_release)

        cnao = deploy_cnao(
            custom_depends,
            cnao_version,
            k8s_provider
        )

        versions["cnao"] = {"enabled": cnao_enabled, "version": cnao[0]}
        cnao_release = cnao[1]

        # Append cnao version to versions dictionary
        depends.append(cnao_release)

        return cnao, cnao_release
    return None, None

cnao, cnao_release = run_cnao()

##################################################################################
# Fetch the Hostpath Provisioner Version
# Deploy Hostpath Provisioner
def run_hostpath_provisioner():
    if hostpath_provisioner_enabled:
        if not cert_manager_enabled:
            pulumi.log.error("Hostpath Provisioner requires Cert Manager to be enabled. Please enable Cert Manager and try again.")
            return None, None

        hostpath_default_path = config.get('hostpath_provisioner.default_path') or "/var/mnt"
        hostpath_default_storage_class = config.get('hostpath_provisioner.default_storage_class') or False
        ns_name = "hostpath-provisioner"
        hostpath_provisioner_version = config.get('hostpath_provisioner.version') or None

        custom_depends = []

        if cilium_enabled:
            custom_depends.append(cilium_release)
        if cert_manager_enabled:
            custom_depends.append(cert_manager_release)
        if kubevirt_enabled:
            custom_depends.append(kubevirt_operator)

        hostpath_provisioner = deploy_hostpath_provisioner(
            custom_depends,
            hostpath_provisioner_version,
            ns_name,
            hostpath_default_path,
            hostpath_default_storage_class,
            k8s_provider,
        )

        versions["hostpath_provisioner"] = {"enabled": hostpath_provisioner_enabled, "version": hostpath_provisioner[0]}
        hostpath_provisioner_release = hostpath_provisioner[1]

        # Append hostpath provisioner version to versions dictionary
        depends.append(hostpath_provisioner_release)

        return hostpath_provisioner, hostpath_provisioner_release
    return None, None

hostpath_provisioner, hostpath_provisioner_release = run_hostpath_provisioner()

##################################################################################
# Deploy Prometheus
def run_prometheus():
    if prometheus_enabled:
        ns_name = "monitoring"
        prometheus_version = config.get('prometheus.version') or None

        prometheus = deploy_prometheus(
            depends,
            ns_name,
            prometheus_version,
            k8s_provider,
            openunison_enabled
        )

        versions["prometheus"] = {"enabled": prometheus_enabled, "version": prometheus[0]}
        prometheus_release = prometheus[1]

        # Append prometheus version to versions dictionary
        depends.append(prometheus_release)

        return prometheus, prometheus_release
    return None, None

prometheus, prometheus_release = run_prometheus()

##################################################################################
# Deploy Containerized Data Importer (CDI)
def run_cdi():
    if cdi_enabled:
        ns_name = "cdi"
        cdi_version = config.get('cdi.version') or None

        cdi = deploy_cdi(
            depends,
            cdi_version,
            k8s_provider
        )

        versions["cdi"] = {"enabled": cdi_enabled, "version": cdi[0]}
        cdi_release = cdi[1]

        # Append cdi version to versions dictionary
        depends.append(cdi_release)

        return cdi, cdi_release
    return None, None

cdi, cdi_release = run_cdi()

##################################################################################
# Deploy Kubernetes Dashboard
def run_kubernetes_dashboard():
    if kubernetes_dashboard_enabled:
        ns_name = "kubernetes-dashboard"
        kubernetes_dashboard_version = config.get('kubernetes_dashboard.version') or None

        if cilium_enabled:
            depends.append(cilium_release)

        kubernetes_dashboard = deploy_kubernetes_dashboard(
            depends,
            ns_name,
            kubernetes_dashboard_version,
            k8s_provider
        )

        versions["kubernetes_dashboard"] = {"enabled": kubernetes_dashboard_enabled, "version": kubernetes_dashboard[0]}
        kubernetes_dashboard_release = kubernetes_dashboard[1]

        depends.append(kubernetes_dashboard_release)

        return kubernetes_dashboard, kubernetes_dashboard_release
    return None, None

kubernetes_dashboard, kubernetes_dashboard_release = run_kubernetes_dashboard()

##################################################################################
def run_openunison():
    if openunison_enabled:
        ns_name = "openunison"
        openunison_version = config.get('openunison.version') or None
        domain_suffix = config.get('openunison.dns_suffix') or "kargo.arpa"
        cluster_issuer = config.get('openunison.cluster_issuer') or "cluster-selfsigned-issuer-ca"

        openunison_github_teams = config.require('openunison.github.teams')
        openunison_github_client_id = config.require('openunison.github.client_id')
        openunison_github_client_secret = config.require('openunison.github.client_secret')

        enabled = {}

        if kubevirt_enabled:
            enabled["kubevirt"] = {"enabled": kubevirt_enabled}

        if prometheus_enabled:
            enabled["prometheus"] = {"enabled": prometheus_enabled}

        pulumi.export("enabled", enabled)

        openunison = deploy_openunison(
            depends,
            ns_name,
            openunison_version,
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
        versions["openunison"] = {"enabled": openunison_enabled, "version": openunison[0]}
        openunison_release = openunison[1]

        depends.append(openunison_release)

        return openunison, openunison_release
    return None, None

openunison, openunison_release = run_openunison()

##################################################################################
# Deploy Rook Ceph
def run_rook_ceph():
    deploy_ceph = config.get_bool('ceph.enabled') or False
    if deploy_ceph:
        rook_operator = deploy_rook_operator(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "rook-ceph"
        )
        return rook_operator
    return None

rook_operator = run_rook_ceph()

##################################################################################
# Deploy Kubevirt Manager
def run_kubevirt_manager():
    kubevirt_manager_enabled = config.get_bool('kubevirt_manager.enabled') or False
    if kubevirt_manager_enabled:
        kubevirt_manager = deploy_ui_for_kubevirt(
            "kargo",
            k8s_provider,
            kubernetes_distribution,
            "kargo",
            "kubevirt_manager"
        )
        pulumi.export('kubevirt_manager', kubevirt_manager)
        return kubevirt_manager
    return None

kubevirt_manager = run_kubevirt_manager()

# Export the component versions
pulumi.export("versions", versions)
