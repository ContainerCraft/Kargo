import requests
import os
import pulumi
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.storage.v1 import StorageClass
from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_ingress_nginx(
        version: str,
        ns_name: str,
        k8s_provider: k8s.Provider,
    ):

    # Create namespace
    # we need to allow privileged containers because nginx wants to be able to run on port 80 and 443
    # because it was designed 1995
    ns_retain = False
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "pod-security.kubernetes.io/enforce": "privileged"
    }
    namespace = create_namespace(
        None,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        custom_labels=ns_labels,
        custom_annotations=ns_annotations
    )

    helm_values = {

    }

    # if we're running in GitHub codespace, run NGINX
    # on port 10443
    if os.getenv("GITHUB_USER"):
        helm_values["controller"] = {
            "service": {
                "type": "ClusterIP",
            },
            "hostPort": {
                "enabled": True,
                    "ports": {
                        "https": 10443,
                    }
            },
            "extraArgs": {
                "https-port": 10443,
            },
            "containerPort": {
                "https": 10443,
            }
        }

    chart_name = "ingress-nginx"
    chart_index_path = "index.yaml"
    chart_url = "https://kubernetes.github.io/ingress-nginx"
    chart_index_url = f"{chart_url}/{chart_index_path}"

    # Fetch the latest version from the helm chart index
    if version is None:
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        version = version.lstrip("v")
        pulumi.log.info(f"Setting helm release version to latest: {chart_name}/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # Deploy the nginx chart
    release = k8s.helm.v3.Release(
        chart_name,
        k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            namespace=ns_name,
            skip_await=False,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=namespace,
            depends_on=[namespace],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="4m",
                delete="4m"
            )
        )
    )

    return release
