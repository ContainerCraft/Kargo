import pulumi
from pulumi_kubernetes import helm, Provider

import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from ...lib.helm_chart_versions import get_latest_helm_chart_version
import json
import secrets
import base64
from kubernetes import config, dynamic
from kubernetes import client as k8s_client
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from kubernetes.client import api_client


def deploy_prometheus(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    # Initialize Pulumi configuration
    pconfig = pulumi.Config()


    # Create a Namespace
    monitoring_namespace = k8s.core.v1.Namespace("monitoring_namespace",
        metadata= k8s.meta.v1.ObjectMetaArgs(
            name="monitoring",
            labels={
                "pod-security.kubernetes.io/enforce":"privileged"
            },
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            retain_on_delete=False,
            custom_timeouts=pulumi.CustomTimeouts(
                create="10m",
                update="10m",
                delete="10m"
            )
        )
    )

    prometheus_helm_values = {}

    openunison_config_enabled = pconfig.get_bool("openunison.enabled") or False

    if (openunison_config_enabled):
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
                                    }


    # Fetch the latest version from the helm chart index
    chart_name = "kube-prometheus-stack"
    chart_index_path = "index.yaml"
    chart_url = "https://prometheus-community.github.io/helm-charts"
    index_url = f"{chart_url}/{chart_index_path}"
    chart_version = get_latest_helm_chart_version(index_url,chart_name)

    prometheus_release = k8s.helm.v3.Release(
            'kube-prometheus-stack',
            k8s.helm.v3.ReleaseArgs(
                chart=chart_name,
                version=chart_version,
                values=prometheus_helm_values,
                namespace='monitoring',
                skip_await=False,
                repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                    repo=chart_url
                ),
            ),
            opts=pulumi.ResourceOptions(
                provider = k8s_provider,
                depends_on=[],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="30m",
                    update="30m",
                    delete="30m"
                )
            )
        )
    # so i can get the release info from OpenUnison to get the right Service name
    pulumi.export("prometheus",prometheus_release)

    # create services with predictable names
    grafana_svc = k8s.core.v1.Service("grafana_service",
                                                    metadata=k8s.meta.v1.ObjectMetaArgs(
                                                        name="grafana",
                                                        namespace="monitoring"
                                                    ),
                                                    spec={
                                                        "selector":{
                                                            "app.kubernetes.io/name":"grafana"
                                                        },
                                                        "ports":[
                                                            {
                                                                "name":"http-web",
                                                                "port": 80,
                                                                "protocol": "TCP",
                                                                "targetPort": 3000

                                                            }
                                                        ],
                                                        "type":"ClusterIP"
                                                    },
                                                    opts=pulumi.ResourceOptions(
                                                                    provider = k8s_provider,
                                                                    retain_on_delete=True,
                                                                    custom_timeouts=pulumi.CustomTimeouts(
                                                                        create="10m",
                                                                        update="10m",
                                                                        delete="10m"
                                                                    )
                                                                )
                                                    )
    alertmanager_svc = k8s.core.v1.Service("alertmanager_service",
                                                metadata=k8s.meta.v1.ObjectMetaArgs(
                                                    name="alertmanager",
                                                    namespace="monitoring"
                                                ),
                                                spec={
                                                    "selector":{
                                                        "app.kubernetes.io/name":"alertmanager"
                                                    },
                                                    "ports":[
                                                        {
                                                            "name":"http-web",
                                                            "port": 9093,
                                                            "protocol": "TCP",
                                                            "targetPort": 9093

                                                        }
                                                    ],
                                                    "type":"ClusterIP"
                                                },
                                                opts=pulumi.ResourceOptions(
                                                                provider = k8s_provider,
                                                                retain_on_delete=True,
                                                                custom_timeouts=pulumi.CustomTimeouts(
                                                                    create="10m",
                                                                    update="10m",
                                                                    delete="10m"
                                                                )
                                                            )
                                                )

    prometheus_svc = k8s.core.v1.Service("prometheus_service",
                                            metadata=k8s.meta.v1.ObjectMetaArgs(
                                                name="prometheus",
                                                namespace="monitoring"
                                            ),
                                            spec={
                                                "selector":{
                                                    "app.kubernetes.io/name":"prometheus"
                                                },
                                                "ports":[
                                                    {
                                                        "name":"http-web",
                                                        "port": 9090,
                                                        "protocol": "TCP",
                                                        "targetPort": 9090

                                                    }
                                                ],
                                                "type":"ClusterIP"
                                            },
                                            opts=pulumi.ResourceOptions(
                                                            provider = k8s_provider,
                                                            retain_on_delete=True,
                                                            custom_timeouts=pulumi.CustomTimeouts(
                                                                create="10m",
                                                                update="10m",
                                                                delete="10m"
                                                            )
                                                        )
                                            )
