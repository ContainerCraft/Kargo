# src/cert_manager/deploy.py
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from typing import Optional, List, Dict, Any, Tuple

from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version
from src.lib.types import NamespaceConfig
from .types import CertManagerConfig

def deploy_cert_manager_module(
        config_cert_manager: CertManagerConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[Optional[str], Optional[pulumi.Resource], Optional[str]]:
    """
    Deploys the Cert Manager module using Helm and manages certificate resources.

    This function handles the orchestration of deploying cert-manager into the Kubernetes
    cluster. It ensures that the appropriate version is deployed using Helm and configures
    necessary resources like the ClusterIssuer for certificate management.

    Args:
        config_cert_manager (CertManagerConfig): Configuration object for cert-manager deployment.
        global_depends_on (List[pulumi.Resource]): A list of resources that the deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.

    Returns:
        Tuple[Optional[str], Optional[pulumi.Resource], Optional[str]]:
            - The deployed cert-manager version.
            - The Helm release resource for cert-manager.
            - The base64-encoded CA certificate from the self-signed issuer.
    """
    # Deploy cert-manager and retrieve the version, Helm release, and CA certificate
    cert_manager_version, release, ca_cert_b64, _ = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    if release:
        # Append the release to global dependencies to maintain resource ordering
        global_depends_on.append(release)

    # Export the CA certificate for use by other modules or consumers
    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)

    return cert_manager_version, release, ca_cert_b64


def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: Optional[List[pulumi.Resource]],
        k8s_provider: k8s.Provider
    ) -> Tuple[str, k8s.helm.v3.Release, str, k8s.core.v1.Secret]:
    """
    Deploys cert-manager into the Kubernetes cluster using a Helm chart.

    This function installs cert-manager via Helm, creates necessary resources such as
    namespaces and self-signed ClusterIssuers, and manages the associated certificate data.

    Args:
        config_cert_manager (CertManagerConfig): Configuration settings for cert-manager.
        depends_on (Optional[List[pulumi.Resource]]): Resources that the deployment should depend on.
        k8s_provider (k8s.Provider): The Kubernetes provider instance.

    Returns:
        Tuple[str, k8s.helm.v3.Release, str, k8s.core.v1.Secret]:
            - The version of cert-manager deployed.
            - The Helm release resource for cert-manager.
            - The base64-encoded CA certificate.
            - The Kubernetes Secret resource containing the CA certificate.
    """
    # Extract configuration details from the CertManagerConfig object
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Validate that a namespace has been provided
    if not namespace:
        raise ValueError("Namespace must be specified in the cert_manager configuration.")

    # Create the namespace for cert-manager based on the provided configuration
    namespace_config = NamespaceConfig(name=namespace)
    namespace_resource = create_namespace(
        config=namespace_config,
        k8s_provider=k8s_provider,
        depends_on=depends_on,
    )

    # Define Helm chart details for cert-manager
    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"

    # Determine which version of cert-manager to deploy
    if version == 'latest' or version is None:
        # Fetch the latest cert-manager version from the Helm chart repository
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name)
        version = version.lstrip("v")  # Remove 'v' prefix if present
        pulumi.log.info(f"Setting Helm release version to latest: {chart_name}/{version}")
    else:
        # Use the provided version
        pulumi.log.info(f"Using Helm release version: {chart_name}/{version}")

    # Generate the values to pass into the Helm chart deployment
    helm_values = gen_helm_values(config_cert_manager)

    # Deploy cert-manager using Helm and return the release resource
    release = k8s.helm.v3.Release(
        chart_name,
        k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            namespace=namespace,
            skip_await=False,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace_resource,
            depends_on=depends_on,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="4m",
                delete="4m"
            )
        )
    )

    # Create a self-signed ClusterIssuer in the cluster
    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": "cluster-selfsigned-issuer-root",
            "namespace": namespace
        },
        spec={
            "selfSigned": {}
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=release,
            depends_on=[namespace_resource],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )

    # Create a certificate signed by the self-signed ClusterIssuer
    cluster_issuer_ca_certificate = CustomResource(
        "cluster-selfsigned-issuer-ca",
        api_version="cert-manager.io/v1",
        kind="Certificate",
        metadata={
            "name": "cluster-selfsigned-issuer-ca",
            "namespace": namespace
        },
        spec={
            "commonName": "cluster-selfsigned-issuer-ca",
            "duration": "2160h0m0s",  # 90 days
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
            "renewBefore": "360h0m0s",  # Renew 15 days before expiration
            "secretName": "cluster-selfsigned-issuer-ca"
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer_root,
            depends_on=[namespace_resource],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )

    # Create the primary ClusterIssuer resource using the CA certificate
    cluster_issuer = CustomResource(
        cluster_issuer_name,
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": cluster_issuer_name,
            "namespace": namespace
        },
        spec={
            "ca": {
                "secretName": cluster_issuer_ca_certificate.spec["secretName"],
            }
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer_ca_certificate,
            depends_on=[namespace_resource],
            custom_timeouts=pulumi.CustomTimeouts(
                create="4m",
                update="4m",
                delete="4m"
            )
        )
    )

    # Retrieve the CA certificate secret generated by cert-manager
    ca_secret = k8s.core.v1.Secret(
        "cluster-selfsigned-issuer-ca-secret",
        metadata={
            "namespace": namespace,
            "name": cluster_issuer_ca_certificate.spec["secretName"]
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer,
            depends_on=[cluster_issuer],
        )
    )

    # Extract the base64-encoded CA certificate from the secret
    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64, ca_secret


def gen_helm_values(
        config_cert_manager: CertManagerConfig
    ) -> Dict[str, Any]:
    """
    Generates custom Helm values for the cert-manager Helm chart.

    This function generates specific Helm chart values based on the provided
    cert-manager configuration. These values are used during Helm deployment
    to customize the resources, including replica counts and resource requests/limits.

    Args:
        config_cert_manager (CertManagerConfig): The configuration for cert-manager.

    Returns:
        Dict[str, Any]: A dictionary of Helm chart values.
    """
    # Define custom values for the cert-manager Helm chart
    helm_values = {
        'replicaCount': 1,  # Set the number of cert-manager replicas
        'installCRDs': config_cert_manager.install_crds,  # Whether to install CRDs
        'resources': {
            'limits': {
                'cpu': '500m',  # CPU resource limit
                'memory': '1024Mi'  # Memory resource limit
            },
            'requests': {
                'cpu': '250m',  # CPU resource request
                'memory': '512Mi'  # Memory resource request
            }
        }
    }
    return helm_values
