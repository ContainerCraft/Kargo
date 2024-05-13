import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def deploy_cert_manager(
        namespace: str,
        k8s_provider: k8s.Provider,
        version: str,
        kubernetes_distribution: str
    ):

    chart_name = "cert-manager"
    chart_index_path = "index.yaml"
    chart_url = "https://charts.jetstack.io"
    chart_index_url = f"{chart_url}/{chart_index_path}"

    # Fetch the latest version from the helm chart index
    if version is None:
        version = get_latest_helm_chart_version(chart_index_url, chart_name)

    # Create namespaces
    name = namespace,
    ns_retain = True
    ns_protect = False
    namespace = create_namespace(
        name,
        k8s_provider,
        ns_retain,
        ns_protect
    )

    # Deploy cert-manager using the Helm release with updated custom values
    helm_values = gen_helm_values(kubernetes_distribution)

    # Deploy cert-manager using the Helm release with custom values
    release = k8s.helm.v3.Release(
        'cert-manager',
        k8s.helm.v3.ReleaseArgs(
            chart='cert-manager',
            version=version,
            namespace=namespace.metadata["name"],
            skip_await=False,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=namespace,
            depends_on=[],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="4m",
                delete="4m"
            )
        )
    )

    # Create a self-signed ClusterIssuer resource
    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": "cluster-selfsigned-issuer-root",
            "namespace": namespace.metadata["name"]
        },
        spec={
            "selfSigned": {}
        },
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[namespace, release],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )

    cluster_issuer_ca_certificate = CustomResource(
        "cluster-selfsigned-issuer-ca",
        api_version="cert-manager.io/v1",
        kind="Certificate",
        metadata={
            "name": "cluster-selfsigned-issuer-ca",
            "namespace": namespace.metadata["name"]
        },
        spec={
            "commonName": "cluster-selfsigned-issuer-ca",
            "duration": "2160h0m0s",
            "isCA": True,
            "issuerRef": {
                "group": "cert-manager.io",
                "kind": "ClusterIssuer",
                "name": cluster_issuer_root.metadata["name"],
            },
            "privateKey": {
                "algorithm": "ECDSA",
                "size": 256
            },
            "renewBefore": "360h0m0s",
            "secretName": "cluster-selfsigned-issuer-ca"
        },
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=cluster_issuer_root,
            depends_on=[],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )

    cluster_issuer = CustomResource(
        "cluster-selfsigned-issuer",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": "cluster-selfsigned-issuer",
            "namespace": namespace.metadata["name"]
        },
        spec={
            "ca": {
                "secretName": cluster_issuer_ca_certificate.spec["secretName"],
            }
        },
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=cluster_issuer_ca_certificate,
            depends_on=[],
            custom_timeouts=pulumi.CustomTimeouts(
                create="4m",
                update="4m",
                delete="4m"
            )
        )
    )

    return version, release

def gen_helm_values(kubernetes_distribution: str):

    # Define custom values for the cert-manager Helm chart
    common_values = {
        'replicaCount': 1,
        'installCRDs': True,
        'resources': {
            'limits': {
                'cpu': '500m',
                'memory': '1024Mi'
            },
            'requests': {
                'cpu': '250m',
                'memory': '512Mi'
            }
        }
    }

    if kubernetes_distribution == 'kind':
        # Kind-specific Helm values
        return {
            **common_values,
        }
    elif kubernetes_distribution == 'talos':
        # Talos-specific Helm values per the Talos Docs
        return {
            **common_values,
        }
    else:
        raise ValueError(f"Unsupported Kubernetes distribution: {kubernetes_distribution}")
