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
from src.vm.ubuntu import deploy_ubuntu_vm
from src.vm.talos import deploy_talos_cluster
from src.ingress_nginx.deploy import deploy_ingress_nginx
from src.kv_manager.deploy import deploy_ui_for_kubevirt

##################################################################################
# Load the Pulumi Config
config = pulumi.Config()

# Get pulumi stack name
stack_name = pulumi.get_stack()

# Get the pulumi project name
project_name = pulumi.get_project()

##################################################################################
# Get the Kubernetes configuration
kubernetes_config = config.get_object("kubernetes") or {}

# Get Kubeconfig from Pulumi ESC Config
kubeconfig = kubernetes_config.get("kubeconfig")

# Require Kubernetes context set explicitly
kubernetes_context = kubernetes_config.get("context")

# Get the Kubernetes distribution (supports: kind, talos)
kubernetes_distribution = kubernetes_config.get("distribution") or "talos"

# Create a Kubernetes provider instance
k8s_provider = Provider(
    "k8sProvider", kubeconfig=kubeconfig, context=kubernetes_context
)

versions = {}

##################################################################################
## Enable/Disable Kargo Kubevirt PaaS Infrastructure Modules
##################################################################################


# Utility function to handle config with default "enabled" flag
def get_module_config(module_name):
    module_config = config.get_object(module_name) or {"enabled": "false"}
    module_enabled = str(module_config.get("enabled")).lower() == "true"
    return module_config, module_enabled


# Get configurations and enabled flags
config_cilium, cilium_enabled = get_module_config("cilium")
config_cert_manager, cert_manager_enabled = get_module_config("cert_manager")
config_kubevirt, kubevirt_enabled = get_module_config("kubevirt")
config_cdi, cdi_enabled = get_module_config("cdi")
config_multus, multus_enabled = get_module_config("multus")
config_prometheus, prometheus_enabled = get_module_config("prometheus")
config_openunison, openunison_enabled = get_module_config("openunison")
config_hostpath_provisioner, hostpath_provisioner_enabled = get_module_config(
    "hostpath_provisioner"
)
config_cnao, cnao_enabled = get_module_config("cnao")
config_kubernetes_dashboard, kubernetes_dashboard_enabled = get_module_config(
    "kubernetes_dashboard"
)
config_kubevirt_manager, kubevirt_manager_enabled = get_module_config(
    "kubevirt_manager"
)
config_vm, vm_enabled = get_module_config("vm")
config_talos, talos_cluster_enabled = get_module_config("talos")

##################################################################################
## Core Kargo Kubevirt PaaS Infrastructure
##################################################################################

depends = []

# defining a separate depends list for openunison to avoid circular dependencies
openunison_depends = []


def safe_append(depends, resource):
    if resource:
        depends.append(resource)


##################################################################################
# Fetch the Cilium Version
# Deploy Cilium
def run_cilium():
    if cilium_enabled:
        namespace = "kube-system"
        l2announcements = config_cilium.get("l2announcements") or "192.168.1.70/28"
        l2_bridge_name = config_cilium.get("l2_bridge_name") or "br0"
        cilium_version = config_cilium.get("version")  # or "1.14.7"
        kubernetes_endpoint_service_address = (
            config_cilium.get("kubernetes_endpoint_service_address") or "localhost"
        )

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

        safe_append(depends, cilium_release)

        versions["cilium"] = {"enabled": cilium_enabled, "version": cilium_version}

        return cilium_version, cilium_release

    return None, None


cilium_version, cilium_release = run_cilium()


##################################################################################
# Fetch the Cert Manager Version
# Deploy Cert Manager
def run_cert_manager():
    if cert_manager_enabled:
        ns_name = "cert-manager"
        cert_manager_version = config_cert_manager.get("version") or None

        cert_manager = deploy_cert_manager(
            ns_name,
            cert_manager_version,
            kubernetes_distribution,
            depends,
            k8s_provider,
        )

        versions["cert_manager"] = {
            "enabled": cert_manager_enabled,
            "version": cert_manager[0],
        }
        cert_manager_release = cert_manager[1]
        cert_manager_selfsigned_cert = cert_manager[2]

        pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)

        safe_append(depends, cert_manager_release)

        return cert_manager, cert_manager_release, cert_manager_selfsigned_cert
    return None, None, None


cert_manager, cert_manager_release, cert_manager_selfsigned_cert = run_cert_manager()


##################################################################################
# Deploy KubeVirt
def run_kubevirt():
    if kubevirt_enabled:
        ns_name = "kubevirt"
        kubevirt_version = config_kubevirt.get("version") or None
        kubevirt_emulation = config_kubevirt.get("emulation") or False

        custom_depends = []
        safe_append(custom_depends, cilium_release)
        safe_append(custom_depends, cert_manager_release)

        kubevirt = deploy_kubevirt(
            custom_depends,
            ns_name,
            kubevirt_version,
            kubevirt_emulation,
            k8s_provider,
            kubernetes_distribution,
        )

        versions["kubevirt"] = {"enabled": kubevirt_enabled, "version": kubevirt[0]}
        kubevirt_operator = kubevirt[1]

        safe_append(openunison_depends, kubevirt_operator)

        return kubevirt, kubevirt_operator
    return None, None


kubevirt, kubevirt_operator = run_kubevirt()


##################################################################################
# Deploy Multus
def run_multus():
    if multus_enabled:
        ns_name = "multus"
        multus_version = config_multus.get("version") or "master"
        bridge_name = config_multus.get("bridge_name") or "br0"

        custom_depends = []

        if cilium_enabled:
            safe_append(custom_depends, cilium_release)
        if cert_manager_enabled:
            safe_append(custom_depends, cert_manager_release)

        multus = deploy_multus(
            custom_depends, multus_version, bridge_name, k8s_provider
        )

        versions["multus"] = {"enabled": multus_enabled, "version": multus[0]}
        multus_release = multus[1]

        safe_append(depends, multus_release)

        return multus, multus_release
    return None, None


multus, multus_release = run_multus()


##################################################################################
# Deploy Cluster Network Addons Operator (CNAO)
def run_cnao():
    if cnao_enabled:
        ns_name = "cluster-network-addons"
        cnao_version = config_cnao.get("version") or None

        custom_depends = []

        if cilium_enabled:
            safe_append(custom_depends, cilium_release)

        if cert_manager_enabled:
            safe_append(custom_depends, cert_manager_release)

        cnao = deploy_cnao(custom_depends, cnao_version, k8s_provider)

        versions["cnao"] = {"enabled": cnao_enabled, "version": cnao[0]}
        cnao_release = cnao[1]

        safe_append(depends, cnao_release)

        return cnao, cnao_release
    return None, None


cnao, cnao_release = run_cnao()


##################################################################################
# Deploy Hostpath Provisioner
def run_hostpath_provisioner():
    if hostpath_provisioner_enabled:
        if not cert_manager_enabled:
            msg = "HPP requires Cert Manager. Please enable Cert Manager and try again."
            pulumi.log.error(msg)
            return None, None

        hostpath_default_path = (
            config_hostpath_provisioner.get("default_path")
            or "/var/mnt/hostpath-provisioner"
        )
        hostpath_default_storage_class = (
            config_hostpath_provisioner.get("default_storage_class") or False
        )
        ns_name = "hostpath-provisioner"
        hostpath_provisioner_version = (
            config_hostpath_provisioner.get("version") or None
        )

        custom_depends = []

        if cilium_enabled:
            safe_append(custom_depends, cilium_release)
        if cert_manager_enabled:
            safe_append(custom_depends, cert_manager_release)
        if kubevirt_enabled:
            safe_append(custom_depends, kubevirt_operator)

        hostpath_provisioner = deploy_hostpath_provisioner(
            custom_depends,
            hostpath_provisioner_version,
            ns_name,
            hostpath_default_path,
            hostpath_default_storage_class,
            k8s_provider,
        )

        versions["hostpath_provisioner"] = {
            "enabled": hostpath_provisioner_enabled,
            "version": hostpath_provisioner[0],
        }
        hostpath_provisioner_release = hostpath_provisioner[1]

        safe_append(depends, hostpath_provisioner_release)

        return hostpath_provisioner, hostpath_provisioner_release
    return None, None


hostpath_provisioner, hostpath_provisioner_release = run_hostpath_provisioner()


##################################################################################
# Deploy Containerized Data Importer (CDI)
def run_cdi():
    if cdi_enabled:
        ns_name = "cdi"
        cdi_version = config_cdi.get("version") or None

        cdi = deploy_cdi(depends, cdi_version, k8s_provider)

        versions["cdi"] = {"enabled": cdi_enabled, "version": cdi[0]}
        cdi_release = cdi[1]

        safe_append(depends, cdi_release)

        return cdi, cdi_release
    return None, None


cdi, cdi_release = run_cdi()


##################################################################################
# Deploy Prometheus
def run_prometheus():
    if prometheus_enabled:
        ns_name = "monitoring"
        prometheus_version = config_prometheus.get("version") or None

        prometheus = deploy_prometheus(
            depends, ns_name, prometheus_version, k8s_provider, openunison_enabled
        )

        versions["prometheus"] = {
            "enabled": prometheus_enabled,
            "version": prometheus[0],
            "release": prometheus[1],
        }
        prometheus_release = prometheus[1]

        safe_append(openunison_depends, prometheus_release)

        return prometheus, prometheus_release
    return None, None


prometheus, prometheus_release = run_prometheus()


##################################################################################
# Deploy Kubernetes Dashboard
def run_kubernetes_dashboard():
    if kubernetes_dashboard_enabled:
        ns_name = "kubernetes-dashboard"
        kubernetes_dashboard_version = (
            config_kubernetes_dashboard.get("version") or None
        )

        if cilium_enabled:
            safe_append(depends, cilium_release)

        kubernetes_dashboard = deploy_kubernetes_dashboard(
            depends,
            ns_name,
            kubernetes_dashboard_version,
            k8s_provider,
            openunison_enabled,
        )

        versions["kubernetes_dashboard"] = {
            "enabled": kubernetes_dashboard_enabled,
            "version": kubernetes_dashboard[0],
            "release": kubernetes_dashboard[1],
        }
        kubernetes_dashboard_release = kubernetes_dashboard[1]

        safe_append(openunison_depends, kubernetes_dashboard_release)

        return kubernetes_dashboard, kubernetes_dashboard_release
    return None, None


kubernetes_dashboard, kubernetes_dashboard_release = run_kubernetes_dashboard()


##################################################################################
# Deploy Kubevirt Manager
def run_kubevirt_manager():
    kubevirt_manager_enabled = config_kubevirt_manager.get("enabled") or False
    if kubevirt_manager_enabled:
        kubevirt_manager = deploy_ui_for_kubevirt(
            "kargo",
            k8s_provider,
        )

        versions["kubevirt_manager"] = {
            "enabled": kubevirt_manager_enabled,
            "version": kubevirt_manager[0],
        }
        kubevirt_manager_release = kubevirt_manager[1]

        safe_append(openunison_depends, kubevirt_manager_release)

        return kubevirt_manager, kubevirt_manager_release

    return None, None


kubevirt_manager, kubevirt_manager_release = run_kubevirt_manager()


##################################################################################
def run_openunison():
    if openunison_enabled:
        ns_name = "openunison"
        openunison_version = config_openunison.get("version") or None
        domain_suffix = config_openunison.get("dns_suffix") or "kargo.arpa"
        cluster_issuer = (
            config_openunison.get("cluster_issuer") or "cluster-selfsigned-issuer-ca"
        )

        config_openunison_github = config_openunison.get("github") or {}
        openunison_github_teams = config_openunison_github.get("teams")
        openunison_github_client_id = config_openunison_github.get("client_id")
        openunison_github_client_secret = config_openunison_github.get("client_secret")

        enabled = {}

        custom_depends = []

        # Assume ingress-nginx for OpenUnison
        nginx_release, nginx_version = deploy_ingress_nginx(
            None, "ingress-nginx", k8s_provider
        )
        versions["nginx"] = {"enabled": openunison_enabled, "version": nginx_version}

        safe_append(custom_depends, nginx_release)

        custom_depends.extend(depends)
        custom_depends.extend(openunison_depends)

        openunison = deploy_openunison(
            custom_depends,
            ns_name,
            openunison_version,
            k8s_provider,
            domain_suffix,
            cluster_issuer,
            cert_manager_selfsigned_cert,
            openunison_github_client_id,
            openunison_github_client_secret,
            openunison_github_teams,
            versions,
        )

        versions["openunison"] = {
            "enabled": openunison_enabled,
            "version": openunison[0],
        }
        openunison_release = openunison[1]

        safe_append(depends, openunison_release)

        return openunison, openunison_release

    return None, None


openunison, openunison_release = run_openunison()


##################################################################################
# Deploy Rook Ceph
def run_rook_ceph():
    deploy_ceph = config.get_bool("ceph.enabled") or False
    if deploy_ceph:
        rook_operator = deploy_rook_operator(
            "kargo", k8s_provider, kubernetes_distribution, "kargo", "rook-ceph"
        )
        return rook_operator
    return None


rook_operator = run_rook_ceph()


##################################################################################
# Deploy Ubuntu VM
def run_ubuntu_vm():
    if vm_enabled:
        # Get the SSH Public Key string from Pulumi Config if it exists
        ssh_pub_key = config.get("ssh_pub_key")
        if not ssh_pub_key:
            # Get the SSH public key from the local filesystem
            with open(f"{os.environ['HOME']}/.ssh/id_rsa.pub", "r") as f:
                ssh_pub_key = f.read().strip()

        # Define the default values
        default_vm_config = {
            "namespace": "default",
            "instance_name": "ubuntu",
            "image_name": "docker.io/containercraft/ubuntu:22.04",
            "node_port": 30590,
            "ssh_user": "kc2",
            "ssh_password": "kc2",
            "ssh_pub_key": ssh_pub_key,
        }

        # Merge the default values with the existing config_vm values
        config_vm_merged = {
            **default_vm_config,
            **{k: v for k, v in config_vm.items() if v is not None},
        }

        # Pass the merged configuration to the deploy_ubuntu_vm function
        ubuntu_vm, ubuntu_ssh_service = deploy_ubuntu_vm(
            config_vm_merged, k8s_provider, depends
        )

        versions["ubuntu_vm"] = {
            "enabled": vm_enabled,
            "name": ubuntu_vm.metadata["name"],
        }

        safe_append(depends, ubuntu_ssh_service)

        return ubuntu_vm, ubuntu_ssh_service
    else:
        return None, None


ubuntu_vm, ubuntu_ssh_service = run_ubuntu_vm()


##################################################################################
# Deploy Kargo-on-Kargo Development Cluster (Controlplane + Worker VirtualMachinePools)
def run_talos_cluster():
    if talos_cluster_enabled:
        # Append the resources to the `depends` list
        custom_depends = []

        # depends on cert manager, multus
        safe_append(custom_depends, cert_manager_release)
        safe_append(custom_depends, multus_release)
        if cdi_enabled:
            safe_append(custom_depends, cdi_release)

        # Deploy the Talos cluster (controlplane and workers)
        controlplane_vm_pool, worker_vm_pool = deploy_talos_cluster(
            config_talos=config_talos,
            k8s_provider=k8s_provider,
            depends_on=custom_depends,
            parent=kubevirt_operator,
        )

        # Export the Talos configuration and versions
        versions["talos_cluster"] = {
            "enabled": talos_cluster_enabled,
            "running": config_talos.get("running", True),
            "controlplane": config_talos.get("controlplane", {}),
            "workers": config_talos.get("workers", {}),
        }

        return controlplane_vm_pool, worker_vm_pool
    else:
        return None, None


# Run the Talos cluster deployment
talos_controlplane_vm_pool, talos_worker_vm_pool = run_talos_cluster()

# Export the component versions
pulumi.export("versions", versions)
