import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource
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
    l2announcements: str,
):
    """
    Deploy Cilium CNI with L2 Announcements enabled

    Args:
        name: Name for the Cilium deployment
        k8s_provider: Kubernetes provider instance
        kubernetes_distribution: Type of k8s distribution (kind, talos)
        project_name: Name of the Pulumi project
        kubernetes_endpoint_service_address: K8s API endpoint address
        namespace: Namespace to deploy Cilium into
        version: Version of Cilium to deploy
        l2_bridge_name: Name of the L2 bridge interface (e.g. br0)
        l2announcements: CIDR block for L2 announcements (e.g. 192.168.1.70/28)

    Returns:
        Tuple containing:
        - Cilium version deployed
        - Cilium Helm release
    """

    # Fetch the latest version of the Cilium Helm chart
    chart_name = "cilium"
    chart_index_url = (
        "https://raw.githubusercontent.com/cilium/charts/master/index.yaml"
    )

    if version is None:
        # Fetch the latest version of the Cilium Helm chart
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(
            f"Setting helm release version to latest: {chart_name}/{version}"
        )
    else:
        # Log the version override
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # Determine Helm values based on the Kubernetes distribution
    helm_values = get_helm_values(
        kubernetes_distribution, project_name, kubernetes_endpoint_service_address
    )

    # Deploy Cilium using the Helm chart
    release = k8s.helm.v3.Release(
        name,
        chart="cilium",
        version=version,
        values=helm_values,
        namespace=namespace,
        repository_opts={"repo": "https://helm.cilium.io/"},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="15m", update="15m", delete="5m"
            ),
        ),
    )

    # Create CiliumL2AnnouncementPolicy for L2 announcements
    cilium_l2_announcement_policy = CustomResource(
        "cilium_l2_announcement_policy",
        api_version="cilium.io/v2alpha1",
        kind="CiliumL2AnnouncementPolicy",
        metadata={"name": "l2-default"},
        spec={
            "serviceSelector": {
                "matchLabels": {}
            },  # Empty matchLabels selects all services
            "interfaces": [l2_bridge_name],  # Interface to announce on (e.g. br0)
            "externalIPs": False,  # Don't announce external IPs
            "loadBalancerIPs": True,  # Announce LoadBalancer IPs
        },
        opts=pulumi.ResourceOptions(
            parent=release,
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    # Create CiliumLoadBalancerIPPool for L2 announcements
    cilium_load_balancer_ip_pool = k8s.apiextensions.CustomResource(
        "cilium_load_balancer_ip_pool",
        api_version="cilium.io/v2alpha1",
        kind="CiliumLoadBalancerIPPool",
        metadata={"name": "l2-default"},
        spec={"blocks": [{"cidr": l2announcements}]},  # CIDR block for L2 announcements
        opts=pulumi.ResourceOptions(
            parent=release,
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    return version, release


def get_helm_values(
    kubernetes_distribution: str,
    project_name: str,
    kubernetes_endpoint_service_address: str,
):
    """
    Get Helm values for Cilium deployment based on k8s distribution

    Args:
        kubernetes_distribution: Type of k8s distribution (kind, talos)
        project_name: Name of the Pulumi project
        kubernetes_endpoint_service_address: K8s API endpoint address

    Returns:
        Dict of Helm values for Cilium deployment
    """
    # Common Cilium Helm Chart Values
    common_values = {
        # "dns": {
        #    "proxyPort": 53,
        # },
        # "dnsProxy": {"enabled": False},
        # "forwardKubeDNSToHost": False,
        "bpf": {
            "masquerade": True,
            "masqueradeInterface": "br0",
            "masqueradeEgressInterface": "br0",
            # bug: https://github.com/cilium/cilium/pull/36852
            # https://docs.cilium.io/en/latest/installation/k8s-install-helm/#install-cilium
            # TODO: bpf bug requires hostLegacyRouting to be true as a workaround for now
            "hostLegacyRouting": True,
        },
        "autoDirectNodeRoutes": True,
        "cgroup": {"autoMount": {"enabled": False}, "hostRoot": "/sys/fs/cgroup"},
        "cluster": {"name": "pulumi"},
        "cni": {"exclusive": False, "install": True},
        "devices": "br+ bond+ thunderbolt+",
        "enableRuntimeDeviceDetection": True,
        "endpointRoutes": {"enabled": True},
        "externalIPs": {"enabled": True},
        "gatewayAPI": {"enabled": False},
        "hostPort": {"enabled": True},
        "hostServices": {"enabled": True},
        "hubble": {
            "enabled": True,
            "relay": {"enabled": True},
            "ui": {"enabled": True},
        },
        "image": {"pullPolicy": "IfNotPresent"},
        "ipam": {"mode": "kubernetes"},
        "ipv4NativeRoutingCIDR": "10.244.0.0/16",
        "k8sClientRateLimit": {"burst": 80, "qps": 40},
        "k8sServiceHost": "127.0.0.1",
        "k8sServicePort": 7445,
        "kubeProxyReplacement": True,
        "l2announcements": {
            "enabled": True,
            "leaseDuration": "15s",
            "leaseRenewDeadline": "5s",
            "leaseRetryPeriod": "2s",
        },
        "loadBalancer": {
            "algorithm": "maglev",
            "mode": "snat",
        },
        "localRedirectPolicy": True,
        "nodePort": {"enabled": True},
        "operator": {"replicas": 1, "rollOutPods": True},
        "rollOutCiliumPods": True,
        "routingMode": "native",
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
                    "SETUID",
                ],
                "cleanCiliumState": ["NET_ADMIN", "SYS_ADMIN", "SYS_RESOURCE"],
            }
        },
        "serviceAccounts": {
            "cilium": {"name": "cilium"},
            "operator": {"name": "cilium-operator"},
        },
        "tunnelProtocol": "vxlan",
        "egressGateway": {
            "enabled": True
        },  # Explicitly enable egress gateway for improved egress traffic handling
        "metrics": {
            "enabled": True
        },  # Enable metrics for cluster and networking performance insights
        "debug": {"enabled": True},  # Enable debug mode for deeper analysis
    }

    # For the kind distribution, we only need to override the k8s service endpoint
    if kubernetes_distribution == "kind":
        return {
            **common_values,
            "k8sServiceHost": kubernetes_endpoint_service_address,
            "k8sServicePort": 6443,
        }
    # For Talos, we're already using all the correct values in common_values
    elif kubernetes_distribution == "talos":
        return common_values
    else:
        raise ValueError(
            f"Unsupported Kubernetes distribution: {kubernetes_distribution}"
        )


# Deploy test loadbalancer service
def deploy_test_service(namespace: str, k8s_provider: k8s.Provider):
    """
    Deploy test nginx pod and LoadBalancer service to validate L2 announcements

    Args:
        namespace: Namespace to deploy test service into
        k8s_provider: Kubernetes provider instance

    Returns:
        Tuple containing:
        - Nginx Pod
        - Nginx LoadBalancer Service
    """

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
            containers=[
                k8s.core.v1.ContainerArgs(
                    name="nginx",
                    image="nginx:latest",
                    ports=[k8s.core.v1.ContainerPortArgs(container_port=80)],
                )
            ]
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )

    # Define nginx LoadBalancer Service resource
    nginx_load_balancer_service = k8s.core.v1.Service(
        "nginx_load_balancer",
        namespace=namespace,
        metadata={"name": "nginx-loadbalancer"},
        spec=k8s.core.v1.ServiceSpecArgs(
            type="LoadBalancer",
            selector={"app": "nginx"},
            ports=[
                k8s.core.v1.ServicePortArgs(protocol="TCP", port=80, target_port=80)
            ],
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )

    return nginx_pod, nginx_load_balancer_service
