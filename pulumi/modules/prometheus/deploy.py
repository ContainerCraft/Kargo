# pulumi/modules/prometheus/deploy.py

"""
Deploys the Prometheus module following the shared design patterns.
"""

import pulumi
import pulumi_kubernetes as k8s
from typing import List, Dict, Any, Tuple, Optional
from core.resource_helpers import create_namespace, create_helm_release
from core.utils import get_latest_helm_chart_version
from .types import PrometheusConfig

def deploy_prometheus_module(
        config_prometheus: PrometheusConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, Optional[pulumi.Resource]]:
    """
    Deploys the Prometheus module and returns the version and the deployed resource.

    Args:
        config_prometheus (PrometheusConfig): Configuration for the Prometheus module.
        global_depends_on (List[pulumi.Resource]): Global dependencies for all modules.
        k8s_provider (k8s.Provider): The Kubernetes provider.

    Returns:
        Tuple[str, Optional[pulumi.Resource]]: The version deployed and the deployed resource.
    """
    prometheus_version, prometheus_resource = deploy_prometheus(
        config_prometheus=config_prometheus,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Update global dependencies
    if prometheus_resource:
        global_depends_on.append(prometheus_resource)

    return prometheus_version, prometheus_resource

def deploy_prometheus(
        config_prometheus: PrometheusConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, Optional[pulumi.Resource]]:
    """
    Deploys Prometheus using Helm and sets up necessary services.
    """
    namespace = config_prometheus.namespace
    version = config_prometheus.version
    openunison_enabled = config_prometheus.openunison_enabled

    # Create Namespace using the helper function
    namespace_resource = create_namespace(
        name=namespace,
        labels=config_prometheus.labels,
        annotations=config_prometheus.annotations,
        k8s_provider=k8s_provider,
        parent=k8s_provider,
        depends_on=depends_on,
    )

    chart_name = "kube-prometheus-stack"
    chart_url = "https://prometheus-community.github.io/helm-charts"
    if version is None or version == "latest":
        version = get_latest_helm_chart_version(chart_url, chart_name)
        pulumi.log.info(f"Setting Prometheus helm chart version to latest release: {version}")
    else:
        pulumi.log.info(f"Using Prometheus helm release version: {version}")

    # Helm values customization based on OpenUnison integration
    prometheus_helm_values = {
        "grafana": {
            "grafana.ini": {
                "users": {
                    "allow_sign_up": False,
                    "auto_assign_org": True,
                    "auto_assign_org_role": "Admin"
                },
                "auth.proxy": {
                    "enabled": True,
                    "header_name": "X-WEBAUTH-USER",
                    "auto_sign_up": True,
                    "headers": "Groups:X-WEBAUTH-GROUPS"
                }
            }
        }
    } if openunison_enabled else {}

    # Create the Helm Release
    release = create_helm_release(
        name=chart_name,
        args=k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            namespace=namespace,
            skip_await=False,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo=chart_url),
            values=prometheus_helm_values,
        ),
        opts=pulumi.ResourceOptions(
            parent=namespace_resource,
        ),
        k8s_provider=k8s_provider,
        depends_on=depends_on,
    )

    # Create Services with predictable names
    services = create_prometheus_services(
        config_prometheus=config_prometheus,
        k8s_provider=k8s_provider,
        namespace=namespace,
        parent=namespace_resource,
        depends_on=[release],
    )

    return version, release

def create_prometheus_services(
        config_prometheus: PrometheusConfig,
        k8s_provider: k8s.Provider,
        namespace: str,
        parent: pulumi.Resource,
        depends_on: List[pulumi.Resource],
    ) -> List[k8s.core.v1.Service]:
    """
    Creates Prometheus, Grafana, and Alertmanager services.

    Args:
        config_prometheus (PrometheusConfig): Configuration for the Prometheus module.
        k8s_provider (k8s.Provider): The Kubernetes provider.
        namespace (str): The namespace to deploy services in.
        parent (pulumi.Resource): The parent resource.
        depends_on (List[pulumi.Resource]): Dependencies for the services.

    Returns:
        List[k8s.core.v1.Service]: The created services.
    """
    services = []

    service_definitions = [
        {
            "name": "grafana",
            "port": 80,
            "targetPort": 3000,
            "selector": "app.kubernetes.io/name",
        },
        {
            "name": "alertmanager",
            "port": 9093,
            "targetPort": 9093,
            "selector": "app.kubernetes.io/name",
        },
        {
            "name": "prometheus",
            "port": 9090,
            "targetPort": 9090,
            "selector": "app.kubernetes.io/name",
        }
    ]

    for service_def in service_definitions:
        service = k8s.core.v1.Service(
            f"service-{service_def['name']}",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=service_def["name"],
                namespace=namespace,
                labels=config_prometheus.labels,
                annotations=config_prometheus.annotations,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                type="ClusterIP",
                ports=[k8s.core.v1.ServicePortArgs(
                    name="http-web",
                    port=service_def["port"],
                    protocol="TCP",
                    target_port=service_def["targetPort"],
                )],
                selector={service_def["selector"]: service_def["name"]},
            ),
            opts=pulumi.ResourceOptions(
                provider=k8s_provider,
                parent=parent,
                depends_on=depends_on,
            )
        )
        services.append(service)

    return services
