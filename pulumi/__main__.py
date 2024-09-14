# __main__.py

# Main entry point for the Kargo Pulumi IaC program.
# This script is responsible for deploying the Kargo platform components located in the respective src/<module_name> directories.

import os
from typing import Any, Dict, List, Optional, Tuple

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider

from src.lib.versions import load_default_versions

##########################################
# Load Pulumi Config and Initialize Variables

# Load the Pulumi configuration settings
config = pulumi.Config()
stack_name = pulumi.get_stack()
project_name = pulumi.get_project()

# Load default versions for modules
default_versions = load_default_versions(config)

# Initialize a dictionary to keep track of deployed component versions
versions: Dict[str, str] = {}

##########################################
# Kubernetes Configuration

# Retrieve Kubernetes settings from Pulumi config or environment variables
kubernetes_config = config.get_object("kubernetes") or {}
kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv('KUBECONFIG')
kubernetes_context = kubernetes_config.get("context")

# Create a Kubernetes provider instance to interact with the cluster
k8s_provider = Provider(
    "k8sProvider",
    kubeconfig=kubeconfig,
    context=kubernetes_context,
)

# Initialize a dictionary to keep track of module configurations
configurations: Dict[str, Dict[str, Any]] = {}

# Log the Kubernetes configuration details
pulumi.log.info(f"kubeconfig: {kubeconfig}")
pulumi.log.info(f"kubernetes_context: {kubernetes_context}")

# TODO: log the git repository URL and branch/commit hash using standard python libraries and pulumi logging functions

##########################################
# Module Configuration and Enable Flags

def get_module_config(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """
    Retrieves and prepares the configuration for a module.

    Args:
        module_name: The name of the module to configure.
        config: The Pulumi configuration object.
        default_versions: A dictionary of default versions for modules.

    Returns:
        A tuple containing the module's configuration dictionary and a boolean indicating if the module is enabled.
    """
    # Get the module's configuration from Pulumi config, default to {"enabled": "false"} if not set
    module_config = config.get_object(module_name) or {"enabled": "false"}
    module_enabled = str(module_config.get('enabled', 'false')).lower() == "true"

    # Remove 'enabled' key from the module configuration as modules do not need this key beyond this point
    module_config.pop('enabled', None)

    # Handle version injection into the module configuration
    module_version = module_config.get('version')
    if not module_version:
        # No version specified in module config; use default version
        module_version = default_versions.get(module_name)
        if module_version:
            module_config['version'] = module_version
        else:
            # No default version available; set to None (module will handle this case)
            module_config['version'] = None
    else:
        # Version is specified in module config; keep as is (could be 'latest' or a specific version)
        pass

    return module_config, module_enabled

##########################################
# Deploy Modules

# Initialize a list to manage dependencies between resources globally
global_depends_on: List[pulumi.Resource] = []

# Cert Manager Module
# Retrieve configuration and enable flag for the cert_manager module
config_cert_manager_dict, cert_manager_enabled = get_module_config('cert_manager', config, default_versions)

if cert_manager_enabled:
    # Import the CertManagerConfig data class and merge the user config with defaults
    from src.cert_manager.types import CertManagerConfig
    config_cert_manager = CertManagerConfig.merge(config_cert_manager_dict)

    # Import the deployment function for the cert_manager module
    from src.cert_manager.deploy import deploy_cert_manager_module

    # Deploy the cert_manager module
    cert_manager_version, cert_manager_release, cert_manager_selfsigned_cert = deploy_cert_manager_module(
        config_cert_manager=config_cert_manager,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Record the deployed version of cert_manager
    versions["cert_manager"] = cert_manager_version

    # Record the configuration state of cert_manager
    configurations["cert_manager"] = {
        "enabled": cert_manager_enabled,
    }

    # Export the self-signed certificate data from cert_manager
    pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)
else:
    cert_manager_selfsigned_cert = None

##########################################
# Export Component Versions and Configurations

# Export the versions of deployed components
pulumi.export("versions", versions)

# Export the configurations of deployed modules
pulumi.export("configuration", configurations)


#import os
#from typing import Any, Dict, List, Optional, Tuple
#
#import pulumi
#import pulumi_kubernetes as k8s
#from pulumi_kubernetes import Provider
#
#from src.cilium.deploy import deploy_cilium
#from src.cert_manager.deploy import deploy_cert_manager
#from src.kubevirt.deploy import deploy_kubevirt
#from src.containerized_data_importer.deploy import deploy_cdi
#from src.cluster_network_addons.deploy import deploy_cnao
#from src.multus.deploy import deploy_multus
#from src.hostpath_provisioner.deploy import deploy as deploy_hostpath_provisioner
#from src.openunison.deploy import deploy_openunison
#from src.prometheus.deploy import deploy_prometheus
#from src.kubernetes_dashboard.deploy import deploy_kubernetes_dashboard
#from src.kv_manager.deploy import deploy_ui_for_kubevirt
#from src.ceph.deploy import deploy_rook_operator
#from src.vm.ubuntu import deploy_ubuntu_vm
#from src.vm.talos import deploy_talos_cluster
#
###########################################
## Load Pulumi Config
#config = pulumi.Config()
#stack_name = pulumi.get_stack()
#project_name = pulumi.get_project()
#
###########################################
## Kubernetes Configuration
#kubernetes_config = config.get_object("kubernetes") or {}
#kubeconfig = kubernetes_config.get("kubeconfig")
#kubernetes_context = kubernetes_config.get("context")
#
## Create a Kubernetes provider instance
#k8s_provider = Provider(
#    "k8sProvider",
#    kubeconfig=kubeconfig,
#    context=kubernetes_context,
#)
#
## Initialize versions dictionary to track deployed component versions
#versions: Dict[str, Dict[str, Any]] = {}
#
###########################################
## Module Configuration and Enable Flags
#def get_module_config(module_name: str) -> Tuple[Dict[str, Any], bool]:
#    """
#    Retrieves the configuration for a module and determines if it is enabled.
#
#    Args:
#        module_name: The name of the module.
#
#    Returns:
#        A tuple containing the module configuration dictionary and a boolean indicating if the module is enabled.
#    """
#    module_config = config.get_object(module_name) or {"enabled": "false"}
#    module_enabled = str(module_config.get('enabled', 'false')).lower() == "true"
#    return module_config, module_enabled
#
## Retrieve configurations and enable flags for all modules
#config_cilium, cilium_enabled = get_module_config('cilium')
#config_cert_manager, cert_manager_enabled = get_module_config('cert_manager')
#config_kubevirt, kubevirt_enabled = get_module_config('kubevirt')
#config_cdi, cdi_enabled = get_module_config('cdi')
#config_multus, multus_enabled = get_module_config('multus')
#config_prometheus, prometheus_enabled = get_module_config('prometheus')
#config_openunison, openunison_enabled = get_module_config('openunison')
#config_hostpath_provisioner, hostpath_provisioner_enabled = get_module_config('hostpath_provisioner')
#config_cnao, cnao_enabled = get_module_config('cnao')
#config_kubernetes_dashboard, kubernetes_dashboard_enabled = get_module_config('kubernetes_dashboard')
#config_kubevirt_manager, kubevirt_manager_enabled = get_module_config('kubevirt_manager')
#config_vm, vm_enabled = get_module_config('vm')
#config_talos, talos_cluster_enabled = get_module_config('talos')
#
###########################################
## Dependency Management
#
## Initialize a list to keep track of dependencies between resources
#global_depends_on: List[pulumi.Resource] = []
#
###########################################
## Module Deployment Functions
#
#def deploy_cert_manager_module() -> Tuple[Optional[str], Optional[pulumi.Resource], Optional[str]]:
#    """
#    Deploys the Cert Manager module if enabled.
#
#    Returns:
#        A tuple containing the version, Helm release, and CA certificate data.
#    """
#    if not cert_manager_enabled:
#        pulumi.log.info("Cert Manager module is disabled. Skipping deployment.")
#        return None, None, None
#
#    namespace = "cert-manager"
#    cert_manager_version = config_cert_manager.get('version')
#
#    cert_manager_version, release, ca_cert_b64, _ = deploy_cert_manager(
#        namespace=namespace,
#        version=cert_manager_version,
#        depends_on=global_depends_on,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["cert_manager"] = {"enabled": cert_manager_enabled, "version": cert_manager_version}
#
#    if release:
#        global_depends_on.append(release)
#
#    # Export the CA certificate
#    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)
#
#    return cert_manager_version, release, ca_cert_b64
#
#cert_manager_version, cert_manager_release, cert_manager_selfsigned_cert = deploy_cert_manager_module()
#
###########################################
## Export Component Versions
#
#pulumi.export("versions", versions)

#def deploy_kubevirt_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the KubeVirt module if enabled.
#
#    Returns:
#        A tuple containing the version and the KubeVirt operator resource.
#    """
#    if not kubevirt_enabled:
#        pulumi.log.info("KubeVirt module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kubevirt"
#    kubevirt_version = config_kubevirt.get('version')
#    kubevirt_emulation = config_kubevirt.get('emulation', False)
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#
#    kubevirt_version, kubevirt_operator = deploy_kubevirt(
#        depends_on=depends_on,
#        namespace=namespace,
#        version=kubevirt_version,
#        emulation=kubevirt_emulation,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["kubevirt"] = {"enabled": kubevirt_enabled, "version": kubevirt_version}
#
#    if kubevirt_operator:
#        global_depends_on.append(kubevirt_operator)
#
#    return kubevirt_version, kubevirt_operator
#
#def deploy_multus_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Multus module if enabled.
#
#    Returns:
#        A tuple containing the version and the Multus Helm release resource.
#    """
#    if not multus_enabled:
#        pulumi.log.info("Multus module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "multus"
#    multus_version = config_multus.get('version', "master")
#    bridge_name = config_multus.get('bridge_name', "br0")
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#
#    multus_version, multus_release = deploy_multus(
#        depends_on=depends_on,
#        version=multus_version,
#        bridge_name=bridge_name,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["multus"] = {"enabled": multus_enabled, "version": multus_version}
#
#    if multus_release:
#        global_depends_on.append(multus_release)
#
#    return multus_version, multus_release
#
#def deploy_hostpath_provisioner_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the HostPath Provisioner module if enabled.
#
#    Returns:
#        A tuple containing the version and the Helm release resource.
#    """
#    if not hostpath_provisioner_enabled:
#        pulumi.log.info("HostPath Provisioner module is disabled. Skipping deployment.")
#        return None, None
#
#    if not cert_manager_enabled:
#        error_msg = "HostPath Provisioner requires Cert Manager. Please enable Cert Manager and try again."
#        pulumi.log.error(error_msg)
#        raise Exception(error_msg)
#
#    namespace = "hostpath-provisioner"
#    hostpath_version = config_hostpath_provisioner.get('version')
#    default_path = config_hostpath_provisioner.get('default_path', "/var/mnt/hostpath-provisioner")
#    default_storage_class = config_hostpath_provisioner.get('default_storage_class', False)
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#    if kubevirt_enabled:
#        depends_on.append(kubevirt_operator)
#
#    hostpath_version, hostpath_release = deploy_hostpath_provisioner(
#        depends_on=depends_on,
#        version=hostpath_version,
#        namespace=namespace,
#        default_path=default_path,
#        default_storage_class=default_storage_class,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["hostpath_provisioner"] = {"enabled": hostpath_provisioner_enabled, "version": hostpath_version}
#
#    if hostpath_release:
#        global_depends_on.append(hostpath_release)
#
#    return hostpath_version, hostpath_release
#
#def deploy_cdi_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Containerized Data Importer (CDI) module if enabled.
#
#    Returns:
#        A tuple containing the version and the CDI Helm release resource.
#    """
#    if not cdi_enabled:
#        pulumi.log.info("CDI module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "cdi"
#    cdi_version = config_cdi.get('version')
#
#    cdi_version, cdi_release = deploy_cdi(
#        depends_on=global_depends_on,
#        version=cdi_version,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["cdi"] = {"enabled": cdi_enabled, "version": cdi_version}
#
#    if cdi_release:
#        global_depends_on.append(cdi_release)
#
#    return cdi_version, cdi_release
#
#def deploy_prometheus_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Prometheus module if enabled.
#
#    Returns:
#        A tuple containing the version and the Prometheus Helm release resource.
#    """
#    if not prometheus_enabled:
#        pulumi.log.info("Prometheus module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "monitoring"
#    prometheus_version = config_prometheus.get('version')
#
#    prometheus_version, prometheus_release = deploy_prometheus(
#        depends_on=global_depends_on,
#        namespace=namespace,
#        version=prometheus_version,
#        k8s_provider=k8s_provider,
#        openunison_enabled=openunison_enabled,
#    )
#
#    versions["prometheus"] = {"enabled": prometheus_enabled, "version": prometheus_version}
#
#    if prometheus_release:
#        global_depends_on.append(prometheus_release)
#
#    return prometheus_version, prometheus_release
#
#def deploy_kubernetes_dashboard_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Kubernetes Dashboard module if enabled.
#
#    Returns:
#        A tuple containing the version and the Dashboard Helm release resource.
#    """
#    if not kubernetes_dashboard_enabled:
#        pulumi.log.info("Kubernetes Dashboard module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kubernetes-dashboard"
#    dashboard_version = config_kubernetes_dashboard.get('version')
#
#    depends_on = global_depends_on.copy()
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#
#    dashboard_version, dashboard_release = deploy_kubernetes_dashboard(
#        depends_on=depends_on,
#        namespace=namespace,
#        version=dashboard_version,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["kubernetes_dashboard"] = {"enabled": kubernetes_dashboard_enabled, "version": dashboard_version}
#
#    if dashboard_release:
#        global_depends_on.append(dashboard_release)
#
#    return dashboard_version, dashboard_release
#
#def deploy_openunison_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the OpenUnison module if enabled.
#
#    Returns:
#        A tuple containing the version and the OpenUnison Helm release resource.
#    """
#    if not openunison_enabled:
#        pulumi.log.info("OpenUnison module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "openunison"
#    openunison_version = config_openunison.get('version')
#    domain_suffix = config_openunison.get('dns_suffix', "kargo.arpa")
#    cluster_issuer = config_openunison.get('cluster_issuer', "cluster-selfsigned-issuer-ca")
#
#    github_config = config_openunison.get('github', {})
#    github_client_id = github_config.get('client_id')
#    github_client_secret = github_config.get('client_secret')
#    github_teams = github_config.get('teams')
#
#    if not github_client_id or not github_client_secret:
#        error_msg = "OpenUnison requires GitHub OAuth credentials. Please provide 'client_id' and 'client_secret' in the configuration."
#        pulumi.log.error(error_msg)
#        raise Exception(error_msg)
#
#    enabled_components = {
#        "kubevirt": {"enabled": kubevirt_enabled},
#        "prometheus": {"enabled": prometheus_enabled},
#    }
#
#    pulumi.export("enabled_components", enabled_components)
#
#    openunison_version, openunison_release = deploy_openunison(
#        depends_on=global_depends_on,
#        namespace=namespace,
#        version=openunison_version,
#        k8s_provider=k8s_provider,
#        domain_suffix=domain_suffix,
#        cluster_issuer=cluster_issuer,
#        ca_cert_b64=cert_manager_selfsigned_cert,
#        kubernetes_dashboard_release=kubernetes_dashboard_release,
#        github_client_id=github_client_id,
#        github_client_secret=github_client_secret,
#        github_teams=github_teams,
#        enabled_components=enabled_components,
#    )
#
#    versions["openunison"] = {"enabled": openunison_enabled, "version": openunison_version}
#
#    if openunison_release:
#        global_depends_on.append(openunison_release)
#
#    return openunison_version, openunison_release
#
#def deploy_ubuntu_vm_module() -> Tuple[Optional[Any], Optional[Any]]:
#    """
#    Deploys an Ubuntu VM using KubeVirt if enabled.
#
#    Returns:
#        A tuple containing the VM resource and the SSH service resource.
#    """
#    if not vm_enabled:
#        pulumi.log.info("Ubuntu VM module is disabled. Skipping deployment.")
#        return None, None
#
#    # Get the SSH public key from Pulumi Config or local filesystem
#    ssh_pub_key = config.get("ssh_pub_key")
#    if not ssh_pub_key:
#        ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
#        try:
#            with open(ssh_key_path, "r") as f:
#                ssh_pub_key = f.read().strip()
#        except FileNotFoundError:
#            error_msg = f"SSH public key not found at {ssh_key_path}. Please provide 'ssh_pub_key' in the configuration."
#            pulumi.log.error(error_msg)
#            raise Exception(error_msg)
#
#    # Merge default VM configuration with user-provided configuration
#    default_vm_config = {
#        "namespace": "default",
#        "instance_name": "ubuntu",
#        "image_name": "docker.io/containercraft/ubuntu:22.04",
#        "node_port": 30590,
#        "ssh_user": "kc2",
#        "ssh_password": "kc2",
#        "ssh_pub_key": ssh_pub_key,
#    }
#
#    vm_config = {**default_vm_config, **config_vm}
#
#    # Deploy the Ubuntu VM
#    ubuntu_vm, ssh_service = deploy_ubuntu_vm(
#        vm_config=vm_config,
#        k8s_provider=k8s_provider,
#        depends_on=global_depends_on,
#    )
#
#    versions["ubuntu_vm"] = {"enabled": vm_enabled, "name": ubuntu_vm.metadata["name"]}
#
#    if ssh_service:
#        global_depends_on.append(ssh_service)
#
#    return ubuntu_vm, ssh_service
#
#def deploy_talos_cluster_module() -> Tuple[Optional[Any], Optional[Any]]:
#    """
#    Deploys a Talos cluster using KubeVirt if enabled.
#
#    Returns:
#        A tuple containing the control plane VM pool and the worker VM pool resources.
#    """
#    if not talos_cluster_enabled:
#        pulumi.log.info("Talos cluster module is disabled. Skipping deployment.")
#        return None, None
#
#    depends_on = []
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#    if multus_enabled:
#        depends_on.append(multus_release)
#    if cdi_enabled:
#        depends_on.append(cdi_release)
#
#    controlplane_vm_pool, worker_vm_pool = deploy_talos_cluster(
#        config_talos=config_talos,
#        k8s_provider=k8s_provider,
#        parent=kubevirt_operator,
#        depends_on=depends_on,
#    )
#
#    versions["talos_cluster"] = {
#        "enabled": talos_cluster_enabled,
#        "running": config_talos.get("running", True),
#        "controlplane": config_talos.get("controlplane", {}),
#        "workers": config_talos.get("workers", {}),
#    }
#
#    return controlplane_vm_pool, worker_vm_pool

# Deactivating Cilium module deployment until Talos 1.8 releases with cni optimizations
#def deploy_cilium_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Cilium CNI module if enabled.
#
#    Returns:
#        A tuple containing the Cilium version and the Helm release resource.
#    """
#    if not cilium_enabled:
#        pulumi.log.info("Cilium module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kube-system"
#    l2_announcements = config_cilium.get('l2announcements', "192.168.1.70/28")
#    l2_bridge_name = config_cilium.get('l2_bridge_name', "br0")
#    cilium_version = config_cilium.get('version')
#
#    # Deploy Cilium using the provided parameters
#    cilium_version, cilium_release = deploy_cilium(
#        name="cilium-cni",
#        provider=k8s_provider,
#        project_name=project_name,
#        kubernetes_endpoint_service_address=None,  # Replace with actual endpoint if needed
#        namespace=namespace,
#        version=cilium_version,
#        l2_bridge_name=l2_bridge_name,
#        l2announcements=l2_announcements,
#    )
#
#    versions["cilium"] = {"enabled": cilium_enabled, "version": cilium_version}
#
#    # Add the release to the global dependencies
#    if cilium_release:
#        global_depends_on.append(cilium_release)
#
#    return cilium_version, cilium_release

#kubevirt_version, kubevirt_operator = deploy_kubevirt_module()
#multus_version, multus_release = deploy_multus_module()
#hostpath_version, hostpath_release = deploy_hostpath_provisioner_module()
#cdi_version, cdi_release = deploy_cdi_module()
#prometheus_version, prometheus_release = deploy_prometheus_module()
#dashboard_version, kubernetes_dashboard_release = deploy_kubernetes_dashboard_module()
#openunison_version, openunison_release = deploy_openunison_module()
#ubuntu_vm, ubuntu_ssh_service = deploy_ubuntu_vm_module()
#talos_controlplane_vm_pool, talos_worker_vm_pool = deploy_talos_cluster_module()
#cilium_version, cilium_release = deploy_cilium_module()
