import pulumi
import pulumi_kubernetes as k8s
from typing import Optional
from src.lib.helm_chart_versions import get_latest_helm_chart_version

import os

# Initialize Pulumi configuration
kubeconfig = os.getenv("KUBECONFIG") or "~/.kube/config"
config = pulumi.Config()

# Try to get the 'kargo:kubernetes.distribution' config value
kubernetes_distribution = config.get('kubernetes')

# Log the detected configuration
pulumi.log.info(f"Detected Configuration: kubernetes = {kubernetes_distribution}")

# Define a default value for kubeconfig_context
kubeconfig_context = "default-context"

# Determine the appropriate Kubernetes context based on the distribution type
if kubernetes_distribution == 'kind':
    kubeconfig_context = "kind-kargo"
elif kubernetes_distribution == 'talos':
    kubeconfig_context = "admin@talos-default"

# Initialize the Kubernetes provider with the chosen context
k8s_provider = k8s.Provider(
    "k8sProvider",
    context=kubeconfig_context,
    kubeconfig=pulumi.Output.secret(kubeconfig),
    suppress_deprecation_warnings=True,
    suppress_helm_hook_warnings=True,
    enable_server_side_apply=True
)

# Define a class to create a Kubernetes namespace for the project
class KubernetesPlatformProject:
    def __init__(self, project_name):
        self.project_name = project_name
        self.namespace = self.create_namespace()

    def create_namespace(self):
        # Create a new namespace with the project name
        return k8s.core.v1.Namespace(
            f"{self.project_name}",
            metadata=k8s.meta.v1.ObjectMetaArgs(name=f"{self.project_name}"),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

# Instantiate the KubernetesPlatformProject class for the 'kargo' project
kubernetes_platform_project = KubernetesPlatformProject("kargo")

# Custom component to fetch Kubernetes API endpoint IPs and join them as a comma-separated string
class KubernetesApiEndpointIp(pulumi.ComponentResource):
    def __init__(self, name: str, k8s_provider: Optional[k8s.Provider] = None, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('custom:x:KubernetesApiEndpointIp', name, {}, opts)

        if not opts:
            opts = pulumi.ResourceOptions()

        if k8s_provider:
            opts.provider = k8s_provider

        self.endpoint = k8s.core.v1.Endpoints.get(
            "kubernetes",
            "kubernetes",
            opts=opts
        )

        # Use apply to extract IP addresses from fetched endpoint
        self.ips = self.endpoint.subsets.apply(
            lambda subsets: [address.ip for subset in subsets for address in subset.addresses] if subsets else []
        )

        # Join multiple IP addresses into a single string
        self.ip_string = self.ips.apply(lambda ips: ','.join(ips) if ips else None)

        self.register_outputs({
            "ip_string": self.ip_string
        })

# To properly create an instance of the custom component, ensure that it is defined before it is instantiated
kubernetes_endpoint_ip = KubernetesApiEndpointIp("k8s-api-ip")

# Helm Values for Kind Kubernetes
cilium_helm_values_kind = {
    "cluster": {
        "name": "kargo.dev"
    },
    "ipam": {
        "mode": "kubernetes"
    },
    "namespace": "kube-system",
    "k8sServiceHost": kubernetes_endpoint_ip.ip_string,
    "k8sServicePort": 6443,
    "kubeProxyReplacement": "strict",
    "operator": {
        "replicas": 1
    },
    "routingMode": "tunnel",
    "serviceAccounts": {
        "cilium": {
            "name": "cilium"
        },
        "operator": {
            "name": "cilium-operator"
        }
    },
}

# Helm Values for Talos Kubernetes per the Talos Cilium Docs
# - https://www.talos.dev/latest/kubernetes-guides/network/deploying-cilium/#method-1-helm-install
cilium_helm_values_talos = {
    "cluster": {
        "name": "kargo.dev"
    },
    "cgroup": {
        "autoMount": {"enabled": False},
        "hostRoot": "/sys/fs/cgroup",
    },
    "namespace": "kube-system",
    "routingMode": "tunnel",
    "k8sServicePort": 7445,
    "tunnelProtocol": "vxlan",
    "k8sServiceHost": "localhost",
    "kubeProxyReplacement": "strict",
    "nativeRoutingCIDR": "10.2.0.0/16",
    "image": {"pullPolicy": "IfNotPresent"},
    "hostServices": {"enabled": False},
    "cluster": {"name": kubernetes_platform_project.project_name},
    "externalIPs": {"enabled": True},
    "gatewayAPI": {"enabled": False},
    "ipam": {"mode": "kubernetes"},
    "nodePort": {"enabled": True},
    "hostPort": {"enabled": True},
    "operator": {"replicas": 1},
    "cni": { "install": True },
    "serviceAccounts": {
        "cilium": {"name": "cilium"},
        "operator": {"name": "cilium-operator"},
    },
    "securityContext": {
        "capabilities": {
            "ciliumAgent": [
                "CHOWN",
                "KILL",
                "NET_ADMIN",
                "NET_RAW",
                "IPC_LOCK",
                "SYS_ADMIN",
                "SYS_RESOURCE",
                "DAC_OVERRIDE",
                "FOWNER",
                "SETGID",
                "SETUID"
            ],
            "cleanCiliumState": [
                "NET_ADMIN",
                "SYS_ADMIN",
                "SYS_RESOURCE"
            ]
        },
    },
}

# Choose the appropriate Helm values
cilium_helm_values = cilium_helm_values_kind if kubernetes_distribution == 'kind' else cilium_helm_values_talos

# Fetch the latest version of the Cilium helm chart
cilium_chart_url = "https://raw.githubusercontent.com/cilium/charts/master/index.yaml"
cilium_chart_name = "cilium"
cilium_latest_version = get_latest_helm_chart_version(cilium_chart_url, cilium_chart_name)

# Deploy Cilium using Helm chart
cilium_helm_release = k8s.helm.v3.Release(
    "cilium-release",
    chart="cilium",
    name="cilium",
    repository_opts={"repo": "https://helm.cilium.io/"},
    version=cilium_latest_version,
    values=cilium_helm_values,
    namespace=cilium_helm_values["namespace"],
    wait_for_jobs=True,
    skip_await=False,
    skip_crds=False,
    lint=True,
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Export the Kubernetes distribution and context as stack outputs
pulumi.export('helm_release_name', cilium_helm_release.resource_names)
pulumi.export('k8s_provider', k8s_provider)
pulumi.export('namespace_name', kubernetes_platform_project.namespace.metadata.name)
pulumi.export('kubeconfig_context', kubeconfig_context)
pulumi.export('kubernetes_distribution', kubernetes_distribution)
pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ip_string)
