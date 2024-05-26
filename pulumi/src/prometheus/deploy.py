import pulumi
import pulumi_kubernetes as k8s
from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_prometheus(
        depends: pulumi.Input[list],
        ns_name: str,
        version: str,
        k8s_provider: k8s.Provider,
        openunison_enabled: bool
    ):

    # Create the monitoring Namespace
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubevirt.io": "",
        "kubernetes.io/metadata.name": ns_name,
        "openshift.io/cluster-monitoring": "true",
        "pod-security.kubernetes.io/enforce": "privileged"
    }
    namespace = create_namespace(
        depends,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        ns_labels,
        ns_annotations
    )

    prometheus_helm_values = {}
    if openunison_enabled:
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
    if version is None:
        chart_index_url = f"{chart_url}/{chart_index_path}"
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(f"Setting version to latest stable: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using {chart_name} version: {version}")

    release = k8s.helm.v3.Release(
        'helm-release-prometheus',
        k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            values=prometheus_helm_values,
            namespace='monitoring',
            skip_await=False,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=namespace,
            depends_on=depends,
            custom_timeouts=pulumi.CustomTimeouts(
                create="30m",
                update="30m",
                delete="30m"
            )
        )
    )
    depends.append(release)

    # create services with predictable names
    service_grafana = k8s.core.v1.Service(
        "service-grafana",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="grafana",
            namespace=ns_name
        ),
        spec={
            "type":"ClusterIP",
            "ports":[
                {
                    "name":"http-web",
                    "port": 80,
                    "protocol": "TCP",
                    "targetPort": 3000

                }
            ],
            "selector":{
                "app.kubernetes.io/name":"grafana"
            }
        },
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=depends,
            retain_on_delete=False,
            provider = k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="3m",
                update="3m",
                delete="3m"
            )
        )
    )

    service_alertmanager = k8s.core.v1.Service(
        "service-alertmanager",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="alertmanager",
            namespace="monitoring"
        ),
        spec={
            "type":"ClusterIP",
            "ports":[
                {
                    "name":"http-web",
                    "port": 9093,
                    "protocol": "TCP",
                    "targetPort": 9093

                }
            ],
            "selector":{
                "app.kubernetes.io/name":"alertmanager"
            }
        },
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=depends,
            provider = k8s_provider,
            retain_on_delete=False,
            custom_timeouts=pulumi.CustomTimeouts(
                create="3m",
                update="3m",
                delete="3m"
            )
        )
    )

    service_prometheus = k8s.core.v1.Service(
        "service-prometheus",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="prometheus",
            namespace="monitoring"
        ),
        spec={
            "type":"ClusterIP",
            "ports":[
                {
                    "name":"http-web",
                    "port": 9090,
                    "protocol": "TCP",
                    "targetPort": 9090

                }
            ],
            "selector":{
                "app.kubernetes.io/name":"prometheus"
            }
        },
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=depends,
            provider = k8s_provider,
            retain_on_delete=False,
            custom_timeouts=pulumi.CustomTimeouts(
                    create="3m",
                    update="3m",
                    delete="3m"
            )
        )
    )

    return version, release
