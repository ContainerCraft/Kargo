import pulumi
import pulumi_kubernetes as k8s
from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_kubernetes_dashboard(
        depends: pulumi.Input[list],
        ns_name: str,
        version: str,
        k8s_provider: k8s.Provider,
    ):

    # Create namespace
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubernetes.io/metadata.name": ns_name
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

    # Fetch the latest version from the helm chart index
    chart_name = "kubernetes-dashboard"
    chart_index_path = "index.yaml"
    chart_url = "https://kubernetes.github.io/dashboard"
    chart_index_url = f"{chart_url}/{chart_index_path}"

    # Fetch the latest version from the helm chart index if version is not set
    if version is None:
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(f"Setting helm release version to latest stable: {chart_name}/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    release = k8s.helm.v3.Release(
            "kubernetes-dashboard",
            k8s.helm.v3.ReleaseArgs(
                chart=chart_name,
                version=version,
                namespace=ns_name,
                skip_await=False,
                repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                    repo=chart_url
                ),
            ),
            opts=pulumi.ResourceOptions(
                provider = k8s_provider,
                parent=namespace,
                depends_on=[namespace],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="8m",
                    update="10m",
                    delete="10m"
                )
            )
        )

    return version, release
