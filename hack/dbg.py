import os
import pulumi
import pulumi_kubernetes as kubernetes
from pulumi_kubernetes import helm

# Initialize Pulumi configuration to read settings from Pulumi.dev.yaml
config = pulumi.Config()

# Retrieve the Kubernetes distribution type (kind or talos) from the configuration
distribution = config.get('kubernetes') or 'talos'

# Determine the appropriate Kubernetes context based on the distribution type
kubeconfig_context = "kind-cilium" if distribution == 'kind' else "admin@talos-default"

# Initialize the Kubernetes provider with the chosen context
k8s_provider = kubernetes.Provider("k8sProvider", kubeconfig=pulumi.Output.secret(os.getenv("KUBECONFIG")), context=kubeconfig_context)

# Define a class to create a Kubernetes namespace for the project
class KubernetesPlatformProject:
    def __init__(self, project_name):
        self.project_name = project_name
        self.namespace = self.create_namespace()

    def create_namespace(self):
        # Create a new namespace with the project name
        return kubernetes.core.v1.Namespace(
            f"{self.project_name}",
            metadata=kubernetes.meta.v1.ObjectMetaArgs(name=f"{self.project_name}"),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

# Instantiate the KubernetesPlatformProject class for the 'kargo' project
kubernetes_platform_project = KubernetesPlatformProject("kargo")

# Function to asynchronously fetch the Kubernetes service IP if the distribution is 'kind'
def get_kubernetes_service_ip():
    kubernetes_service = kubernetes.core.v1.Service.get(
        "k8s-service", "kubernetes",
        pulumi.ResourceOptions(provider=k8s_provider))
    return kubernetes_service.spec.cluster_ip if kubernetes_service.spec else "localhost"

# Fetch the Kubernetes service IP based on the distribution type
kubernetes_service_ip = pulumi.Output.from_input(get_kubernetes_service_ip()) if distribution == 'kind' else "localhost"

# Helm Values for Kind Kubernetes
cilium_helm_values_kind = {
    "cluster": {
        "name": "kind-cilium"
    },
    "ipam": {
        "mode": "kubernetes"
    },
    "namespace": "kube-system",
    "k8sServiceHost": kubernetes_service_ip,
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
cilium_helm_values = cilium_helm_values_kind if distribution == 'kind' else cilium_helm_values_talos

# Deploy Cilium using Helm chart
cilium_helm_release = helm.v3.Release(
    "cilium-release",
    chart="cilium",
    name="cilium",
    repository_opts={"repo": "https://helm.cilium.io/"},
    version="1.14.5",
    values=cilium_helm_values,
    namespace=cilium_helm_values["namespace"],
    wait_for_jobs=True,
    skip_await=False,
    skip_crds=False,
    lint=True,
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Export necessary Pulumi stack outputs
pulumi.export('kubernetes_distribution', distribution)
pulumi.export('namespace_name', kubernetes_platform_project.namespace.metadata.name)
pulumi.export("ciliumResources", cilium_helm_release.resource_names)
pulumi.export("ciliumReleaseName", cilium_helm_release.status.apply(lambda s: s.name))
