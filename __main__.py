import pulumi
import pulumi_kubernetes as k8s
from src.lib.helm_chart_versions import get_latest_helm_chart_version
from src.kargo.cilium import deploy as deploy_cilium
import os

# Initialize Pulumi configuration
kubeconfig = os.getenv("KUBECONFIG") #or "~/.kube/config"
config = pulumi.Config()

kubernetes_distribution = config.require('kubernetes')
kubeconfig_context = config.require('kubecontext')

# Enhanced debugging: Log configuration
pulumi.log.info(f"cfg: KUBECONFIG: {kubeconfig}")
pulumi.log.info(f"cfg: Kubernetes distribution: {kubernetes_distribution}")
pulumi.log.info(f"cfg: kubeconfig_context: {kubeconfig_context}")

# Initialize the Kubernetes provider with the chosen contextd
k8s_provider = k8s.Provider(
    "k8sProvider",
    context=kubeconfig_context,
    kubeconfig=kubeconfig,
    suppress_deprecation_warnings=True,
    suppress_helm_hook_warnings=True,
    enable_server_side_apply=True
)

class KubernetesPlatformProject:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.namespace = self.create_namespace()

    def create_namespace(self):
        return k8s.core.v1.Namespace(
            f"{self.project_name}",
            metadata=k8s.meta.v1.ObjectMetaArgs(name=self.project_name),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

kubernetes_platform_project = KubernetesPlatformProject("kargo")

class KubernetesApiEndpointIp(pulumi.ComponentResource):
    def __init__(self, name: str, k8s_provider: k8s.Provider):
        super().__init__('custom:x:KubernetesApiEndpointIp', name, {}, opts=pulumi.ResourceOptions(provider=k8s_provider))

        self.endpoint = k8s.core.v1.Endpoints.get(
            "kubernetes",
            "kubernetes",
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

        self.ips = self.endpoint.subsets.apply(
            lambda subsets: ','.join([address.ip for subset in subsets for address in subset.addresses]) if subsets else ''
        )

        self.register_outputs({"ip_string": self.ips})

kubernetes_endpoint_ip = KubernetesApiEndpointIp("k8s-api-ip", k8s_provider)

cilium_helm_release = deploy_cilium(
    "cilium-release",
    k8s_provider,
    kubernetes_distribution,
    "kargo",
    kubernetes_endpoint_ip.ips,
    "kube-system"
)

pulumi.export('helm_release_name', cilium_helm_release.resource_names)
pulumi.export('k8s_provider', k8s_provider)
pulumi.export('namespace_name', kubernetes_platform_project.namespace.metadata.name)
pulumi.export('kubeconfig_context', kubeconfig_context)
pulumi.export('kubernetes_distribution', kubernetes_distribution)
pulumi.export('kubernetes_endpoint_ips', kubernetes_endpoint_ip.ips)
