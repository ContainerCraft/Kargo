import pulumi
import pulumi_kubernetes as k8s
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_cilium(
        name: str,
        k8s_provider: k8s.Provider,
        kubernetes_distribution: str,
        project_name: str,
        kubernetes_endpoint_service_address: pulumi.Output[str],
        namespace: str,
        version: str,
        l2_bridge_name: str,
        l2announcements: str
    ):

    # Fetch the latest version of the Cilium Helm chart
    chart_name = "cilium"
    chart_index_url = "https://raw.githubusercontent.com/cilium/charts/master/index.yaml"

    if version is None:
        # Fetch the latest version of the Cilium Helm chart
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(f"Setting helm release version to latest: {chart_name}/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # Determine Helm values based on the Kubernetes distribution
    helm_values = get_helm_values(kubernetes_distribution, project_name, kubernetes_endpoint_service_address)

    # Deploy Cilium using the Helm chart
    release = k8s.helm.v3.Release(
        name,
        chart="cilium",
        version=version,
        values=helm_values,
        namespace=namespace,
        repository_opts={"repo": "https://helm.cilium.io/"},
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    cilium_l2_announcement_policy = k8s.apiextensions.CustomResource(
        "cilium_l2_announcement_policy",
        api_version="cilium.io/v2alpha1",
        kind="CiliumL2AnnouncementPolicy",
        metadata={"name": "l2-default"},
        spec={
            "serviceSelector": {"matchLabels": {}},
            "interfaces": [l2_bridge_name],
            "externalIPs": False,
            "loadBalancerIPs": True
        },
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Define CiliumLoadBalancerIPPool resource
    cilium_load_balancer_ip_pool = k8s.apiextensions.CustomResource(
        "cilium_load_balancer_ip_pool",
        api_version="cilium.io/v2alpha1",
        kind="CiliumLoadBalancerIPPool",
        metadata={"name": "l2-default"},
        spec={
            "cidrs": [{"cidr": l2announcements}]
        },
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return version, release

def get_helm_values(
        kubernetes_distribution: str,
        project_name: str,
        kubernetes_endpoint_service_address: str
    ):
    # Common Cilium Helm Chart Values
    common_values = {
        "cluster": {
            "id": 1,
            "name": project_name
        },
        "routingMode": "tunnel",
        "tunnelProtocol": "vxlan",
        "kubeProxyReplacement": "strict",
        "image": {"pullPolicy": "IfNotPresent"},
        "l2announcements": {"enabled": True},
        "hostServices": {"enabled": False},
        "cluster": {"name": "pulumi"},
        "externalIPs": {"enabled": True},
        "gatewayAPI": {"enabled": False},
        "hubble": {
            "enabled": True,
            "relay": {"enabled": True},
            "ui": {"enabled": True},
        },
        "ipam": {"mode": "kubernetes"},
        "nodePort": {"enabled": True},
        "hostPort": {"enabled": True},
        "operator": {"replicas": 1},
        "serviceAccounts": {
            "cilium": {"name": "cilium"},
            "operator": {"name": "cilium-operator"},
        },
    }
    # Kind Kubernetes specific Helm values
    if kubernetes_distribution == 'kind':
        return {
            **common_values,
            "k8sServiceHost": kubernetes_endpoint_service_address,
            "k8sServicePort": 6443,
        }
    elif kubernetes_distribution == 'talos':
        # Talos-specific Helm values per the Talos Cilium Docs
        return {
            **common_values,
            "autoDirectNodeRoutes": True,
            "containerRuntime": {"integration": "containerd"},
            "devices": "br+ bond+ thunderbolt+",
            "enableRuntimeDeviceDetection": True,
            "endpointRoutes": {"enabled": True},
            "bpf": {"masquerade": True},
            "localRedirectPolicy": True,
            "loadBalancer": {
                "algorithm": "maglev",
                "mode": "dsr"
            },
            "cgroup": {
                "autoMount": {"enabled": False},
                "hostRoot": "/sys/fs/cgroup",
            },
            "routingMode": "native",
            "ipv4NativeRoutingCIDR": "10.244.0.0/16",
            "k8sServicePort": 7445,
            "tunnelProtocol": "vxlan",
            "k8sServiceHost": "127.0.0.1",
            "kubeProxyReplacement": "true",
            "image": {"pullPolicy": "IfNotPresent"},
            "hostServices": {"enabled": False},
            "externalIPs": {"enabled": True},
            "gatewayAPI": {"enabled": False},
            "nodePort": {"enabled": True},
            "hostPort": {"enabled": True},
            "rollOutCiliumPods": True,
            "operator": {
                "replicas": 1,
                "rollOutPods": True,
            },
            "cni": {
                "install": True,
                "exclusive": False
            },
            "securityContext": {
                "capabilities": {
                    "ciliumAgent": [
                        "CHOWN", "KILL", "NET_ADMIN", "NET_RAW", "IPC_LOCK",
                        "SYS_ADMIN", "SYS_RESOURCE", "DAC_OVERRIDE", "FOWNER",
                        "SETGID", "SETUID"
                    ],
                    "cleanCiliumState": ["NET_ADMIN", "SYS_ADMIN", "SYS_RESOURCE"],
                },
            },
        }
    else:
        raise ValueError(f"Unsupported Kubernetes distribution: {kubernetes_distribution}")

# Deploy test loadbalancer service
def deploy_test_service(
        namespace: str,
        k8s_provider: k8s.Provider
    ):

    # Development only:
    # nginx pod and loadbalancer service resources are being committed
    # to test the Cilium L2 announcement policy and LoadBalancerIPPool
    # These resources will be removed before MVP release.
    # Define nginx Pod resource
    nginx_pod = k8s.core.v1.Pod(
        "nginx_pod",
        namespace=namespace,
        metadata={"name": "nginx", "labels": {"app": "nginx"}},
        spec=k8s.core.v1.PodSpecArgs(
            containers=[k8s.core.v1.ContainerArgs(
                name="nginx",
                image="nginx:latest",
                ports=[k8s.core.v1.ContainerPortArgs(container_port=80)]
            )]
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Define nginx LoadBalancer Service resource
    nginx_load_balancer_service = k8s.core.v1.Service(
        "nginx_load_balancer",
        namespace=namespace,
        metadata={"name": "nginx-loadbalancer"},
        spec=k8s.core.v1.ServiceSpecArgs(
            type="LoadBalancer",
            selector={"app": "nginx"},
            ports=[k8s.core.v1.ServicePortArgs(
                protocol="TCP",
                port=80,
                target_port=80
            )]
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return nginx_pod, nginx_load_balancer_service
