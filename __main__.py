import pulumi
import os
import pulumi_kubernetes as kubernetes
from pulumi_kubernetes import Provider, core, helm, apps

config = pulumi.Config()
context = config.get("kubeconfig.context") or "admin@talos-default"
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

# Using Helm Values per Talos Docs
# - https://www.talos.dev/latest/kubernetes-guides/network/deploying-cilium/#method-1-helm-install
cilium_helm_values = {
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
    opts=pulumi.ResourceOptions(
        provider=k8s_provider
    )
)

pulumi.export("ciliumResources", cilium_helm_release.resource_names)
pulumi.export("ciliumReleaseName", cilium_helm_release.status.apply(lambda s: s.name))
