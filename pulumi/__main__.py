import pulumi
import os
import pulumi_kubernetes as kubernetes
from pulumi_kubernetes import Provider, core, helm, apps

# lazily setting variables for now
cluster_ip = "192.168.1.41"

config = pulumi.Config()
context = config.get_secret("kubeconfig.context") or "admin@kargo.dev"
k8s_provider = kubernetes.Provider("k8sProvider", kubeconfig=pulumi.Output.secret(os.getenv("KUBECONFIG")), context=context)

class KubernetesPlatformProject:
    def __init__(self, project_name):
        self.project_name = project_name
        self.namespace = self.create_namespace()

    def create_namespace(self):
        return kubernetes.core.v1.Namespace(
            f"{self.project_name}",
            metadata=kubernetes.meta.v1.ObjectMetaArgs(
                name=f"{self.project_name}"
            ),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

kubernetes_platform_project = KubernetesPlatformProject("kargo")

pulumi.export('namespace_name', kubernetes_platform_project.namespace.metadata.name)

cilium_helm_values = {
    "cluster": {
      "name": "kargo.dev"
    },
    "namespace": "kube-system",
    "routingMode": "tunnel",
    "k8sServicePort": 6443,
    "tunnelProtocol": "vxlan",
    "k8sServiceHost": "192.168.1.40",
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
    "serviceAccounts": {
        "cilium": {"name": "cilium"},
        "operator": {"name": "cilium-operator"},
    },
}

cilium_helm_release = helm.v3.Release("cilium-release",
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
                                      opts=pulumi.ResourceOptions(provider=k8s_provider))

pulumi.export("ciliumResources", cilium_helm_release.resource_names)
pulumi.export("ciliumReleaseName", cilium_helm_release.status.apply(lambda s: s.name))
pulumi.export("clusterIP", cluster_ip)
