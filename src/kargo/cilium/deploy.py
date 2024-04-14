import pulumi
import pulumi_kubernetes as k8s
from typing import Optional
from ...lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_cilium(name: str, k8s_provider: k8s.Provider, kubernetes_distribution: str, project_name: str, kubernetes_endpoint_ip_string: str, namespace: str, l2_bridge_name: str, l2announcements: str):
    """
    Deploy Cilium using the Helm chart.

    Args:
        name (str): The name of the release.
        k8s_provider (Provider): The Kubernetes provider.
        kubernetes_distribution (str): The Kubernetes distribution.
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.
        namespace (str): The namespace to deploy Cilium to.

    Returns:
        pulumi.helm.v3.Release: The deployed Cilium Helm release.
    """
    # Determine Helm values based on the Kubernetes distribution
    helm_values = get_helm_values(kubernetes_distribution, project_name, kubernetes_endpoint_ip_string)

    # Fetch the latest version of the Cilium Helm chart
    cilium_chart_url = "https://raw.githubusercontent.com/cilium/charts/master/index.yaml"
    cilium_chart_name = "cilium"
    cilium_latest_version = get_latest_helm_chart_version(cilium_chart_url, cilium_chart_name)

    # Statically limit the Cilium version to 1.14.7 until resolved
    #cilium_latest_version = "1.14.7"

    # Deploy Cilium using the Helm chart
    deploy_cilium_release = k8s.helm.v3.Release(
        name,
        chart="cilium",
        version=cilium_latest_version,
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

    ## Development only:
    # nginx pod and loadbalancer service resources are being committed
    # to test the Cilium L2 announcement policy and LoadBalancerIPPool
    # These resources will be removed before MVP release.
    # Define nginx Pod resource
    nginx_pod = k8s.core.v1.Pod(
        "nginx_pod",
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

def get_helm_values(
        kubernetes_distribution: str,
        project_name: str,
        kubernetes_endpoint_ip_string: str):

    common_values = {
        "cluster": {
            "id": 1,
            "name": project_name
        },
        "ipam": {"mode": "kubernetes"},
        "serviceAccounts": {
            "cilium": {"name": "cilium"},
            "operator": {"name": "cilium-operator"},
        },
        "l2announcements": {"enabled": True},
    }

    if kubernetes_distribution == 'talos':
        # Talos-specific Helm values per the Talos Cilium Docs
        return {
            **common_values,
            "cni": {
                "install": True,
                "exclusive": False
            },
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

    elif kubernetes_distribution == 'kind':
        return {
            **common_values,
            "k8sServiceHost": kubernetes_endpoint_ip_string,
            "k8sServicePort": 6443,
            "kubeProxyReplacement": "strict",
            "operator": {"replicas": 1},
            "routingMode": "tunnel",
        }
    else:
        raise ValueError(f"Unsupported Kubernetes distribution: {kubernetes_distribution}")
