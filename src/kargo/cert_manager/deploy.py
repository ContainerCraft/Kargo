import pulumi
from pulumi_kubernetes import helm, Provider
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from ...lib.helm_chart_versions import get_latest_helm_chart_version

def deploy(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    # Create a Namespace
    cert_manager_namespace = k8s.core.v1.Namespace("cert_manager_namespace",
        metadata= k8s.meta.v1.ObjectMetaArgs(
            name="cert-manager"
        ),
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

    # Fetch the latest version from the helm chart index
    chart_name = "cert-manager"
    chart_index_path = "index.yaml"
    chart_url = "https://charts.jetstack.io"
    index_url = f"{chart_url}/{chart_index_path}"
    chart_version = get_latest_helm_chart_version(index_url, chart_name)

    # Deploy cert-manager using the Helm release with updated custom values
    helm_values = gen_helm_values(kubernetes_distribution, project_name)

    release = k8s.helm.v3.Release(
        'cert-manager',
        k8s.helm.v3.ReleaseArgs(
            chart='cert-manager',
            version='1.3.0',
            namespace='cert-manager',
            skip_await=False,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[cert_manager_namespace],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )

    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": "cluster-selfsigned-issuer-root",
            "namespace": "cert-manager"
        },
        spec={
            "selfSigned": {}
        },
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[release],
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
            "namespace": "cert-manager"
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
            depends_on=[cluster_issuer_root],
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
            "namespace": "cert-manager"
        },
        spec={
            "ca": {
                "secretName": cluster_issuer_ca_certificate.spec["secretName"],
            }
        },
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[cluster_issuer_ca_certificate],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )
    ## wait for helm release to be deployed
    #helm_deploy = cert_manager_release.status["status"].apply(lambda status: status == "deployed")
    #return cert_manager_release

    ## Deploy Rook Ceph Operator using the Helm chart
    #release = helm.v3.Release(
    #    name,
    #    chart="rook-ceph",
    #    version=chart_version,
    #    #values=helm_values,
    #    values={},
    #    namespace=namespace,
    #    repository_opts={"repo": "https://charts.rook.io/release"},
    #    opts=pulumi.ResourceOptions(provider = k8s_provider)
    #)

    return(release, chart_version)

def gen_helm_values(kubernetes_distribution: str, project_name: str):
    """
    Get the Helm values for installing Rook Ceph based on the specified Kubernetes distribution.

    Args:
        kubernetes_distribution (str): The Kubernetes distribution (e.g., 'kind', 'talos').
        project_name (str): The name of the project.
        kubernetes_endpoint_ip_string (str): The IP address of the Kubernetes endpoint.

    Returns:
        dict: The Helm values for installing Rook Ceph.

    Raises:
        ValueError: If the specified Kubernetes distribution is not supported.
    """

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
