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

    # 1. Set up base configuration
    if version is None:
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(
            f"Setting helm release version to latest: {chart_name}/{version}"
        )
    else:
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # 2. Create Gateway API CRDs first (must be done before anything else)
    gateway_crds = k8s.yaml.ConfigFile(
        "gateway-api-crds",
        file="https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml",
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )

    # 3. Prepare Helm values
    base_values = get_helm_values(
        kubernetes_distribution, project_name, kubernetes_endpoint_service_address
    )

    helm_values = {
        **base_values,
        "gatewayAPI": {
            "enabled": True,
            "controller": {"enabled": True, "replicas": 1},
        },
        "ingressController": {
            "enabled": True,
            "loadbalancerMode": "shared",
            "service": {"type": "LoadBalancer", "annotations": {}},
            "default": True,
            "enableGatewayAPI": True,
        },
        "hubble": {
            "enabled": True,
            "relay": {"enabled": True},
            "ui": {
                "enabled": True,
                "service": {"type": "ClusterIP", "ports": {"http": 80}},
            },
        },
    }

    # 4. Deploy Cilium with Helm (depends on CRDs)
    release = k8s.helm.v3.Release(
        name,
        chart="cilium",
        version=version,
        values=helm_values,
        namespace=namespace,
        repository_opts={"repo": "https://helm.cilium.io/"},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[gateway_crds],
            custom_timeouts=pulumi.CustomTimeouts(
                create="15m", update="15m", delete="5m"
            ),
        ),
    )

    # 5. Create L2 announcement resources (depends on Cilium release)
    cilium_load_balancer_ip_pool = k8s.apiextensions.CustomResource(
        "cilium-l2-ip-pool",
        api_version="cilium.io/v2alpha1",
        kind="CiliumLoadBalancerIPPool",
        metadata={
            "name": "l2-default",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "pulumi",
                "app.kubernetes.io/name": name,
            },
        },
        spec={"blocks": [{"cidr": l2announcements}]},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[release],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    cilium_l2_announcement_policy = CustomResource(
        "cilium-l2-policy",
        api_version="cilium.io/v2alpha1",
        kind="CiliumL2AnnouncementPolicy",
        metadata={
            "name": "l2-default",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "pulumi",
                "app.kubernetes.io/name": name,
            },
        },
        spec={
            "serviceSelector": {"matchLabels": {}},
            "interfaces": [l2_bridge_name],
            "externalIPs": False,
            "loadBalancerIPs": True,
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[release, cilium_load_balancer_ip_pool],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    # 6. Create Hubble Gateway resources (depends on Cilium and L2 resources)
    gateway, http_route = create_hubble_gateway(
        name=name,
        namespace=namespace,
        k8s_provider=k8s_provider,
        l2announcements=l2announcements,
        depends_on=[
            release,
            cilium_load_balancer_ip_pool,
            cilium_l2_announcement_policy,
        ],
    )

    return version, release, gateway, http_route


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
        "autoDirectNodeRoutes": True,
        "bpf": {
            "masquerade": True,
            "masqueradeInterface": "br0",
            "masqueradeEgressInterface": "br0",
            # bug: https://github.com/cilium/cilium/pull/36852
            # https://docs.cilium.io/en/latest/installation/k8s-install-helm/#install-cilium
            # TODO: bpf bug requires hostLegacyRouting to be true as a workaround for now
            "hostLegacyRouting": True,
        },
        "cgroup": {"autoMount": {"enabled": False}, "hostRoot": "/sys/fs/cgroup"},
        "cluster": {"name": "pulumi"},
        "cni": {"exclusive": False, "install": True},
        "devices": "br+ bond+ thunderbolt+",
        "enableRuntimeDeviceDetection": True,
        "endpointRoutes": {"enabled": True},
        "externalIPs": {"enabled": True},
        "gatewayAPI": {
            "enabled": True,
            "secretsNamespace": {"create": False, "name": "cilium-secrets"},
        },
        "hostPort": {"enabled": True},
        "hostServices": {"enabled": True},
        "ingressController": {
            "enabled": True,
            "loadbalancerMode": "shared",
            "service": {"type": "LoadBalancer", "annotations": {}},
            "enableGatewayAPI": True,
        },
        "egressGateway": {
            "enabled": True,
            "secretsNamespace": {"create": False, "name": "cilium-secrets"},
            "controller": {"enabled": True, "replicas": 1},
        },
        "hubble": {
            "enabled": True,
            "relay": {"enabled": True},
            "ui": {
                "enabled": True,
                "service": {"type": "ClusterIP", "ports": {"http": 80}},
            },
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
        # Use snat, do not use dsr due to extreme performance degredation
        "loadBalancer": {"algorithm": "maglev", "mode": "snat"},
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
        "metrics": {"enabled": True},
        "debug": {"enabled": True},
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


def create_hubble_gateway(
    name: str,
    namespace: str,
    k8s_provider: k8s.Provider,
    l2announcements: str,
    depends_on: list = None,
):
    """Create Gateway API resources for Hubble UI

    Args:
        name: Name prefix for Gateway resources
        namespace: Namespace to deploy Gateway into
        k8s_provider: Kubernetes provider instance
        l2announcements: CIDR block for L2 announcements
        depends_on: List of resources to depend on
    """
    gateway = k8s.apiextensions.CustomResource(
        f"{name}-hubble-gateway",
        api_version="gateway.networking.k8s.io/v1",
        kind="Gateway",
        metadata={
            "name": f"{name}-hubble-gateway",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "pulumi",
                "app.kubernetes.io/name": name,
            },
        },
        spec={
            "gatewayClassName": "cilium",
            "listeners": [
                {
                    "name": "http",
                    "protocol": "HTTP",
                    "port": 80,
                    "allowedRoutes": {"namespaces": {"from": "Same"}},
                }
            ],
            "addresses": [
                {"type": "IPAddress", "value": l2announcements.split("/")[0]}
            ],
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
        ),
    )

    http_route = k8s.apiextensions.CustomResource(
        f"{name}-hubble-route",
        api_version="gateway.networking.k8s.io/v1",
        kind="HTTPRoute",
        metadata={
            "name": f"{name}-hubble-route",
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "pulumi",
                "app.kubernetes.io/name": name,
            },
        },
        spec={
            "parentRefs": [{"name": gateway.metadata["name"], "namespace": namespace}],
            "rules": [
                {
                    "matches": [{"path": {"type": "PathPrefix", "value": "/"}}],
                    "backendRefs": [{"name": "hubble-ui", "port": 80}],
                }
            ],
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[gateway],
        ),
    )

    return gateway, http_route
