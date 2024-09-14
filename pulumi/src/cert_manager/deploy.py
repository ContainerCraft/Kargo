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
    Deploys the Cert Manager module if enabled.

    Returns:
        A tuple containing the version, Helm release, and CA certificate data.
    """
    cert_manager_version, release, ca_cert_b64, _ = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    if release:
        global_depends_on.append(release)

    # Export the CA certificate
    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)

    return cert_manager_version, release, ca_cert_b64

def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: Optional[List[pulumi.Resource]],
        k8s_provider: k8s.Provider
    ) -> Tuple[str, k8s.helm.v3.Release, str, k8s.core.v1.Secret]:
    # Extract configuration values
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Validate required fields
    if not namespace:
        raise ValueError("Namespace must be specified in the cert_manager configuration.")

    # Create NamespaceConfig instance
    namespace_config = NamespaceConfig(name=namespace)

    # Create namespace using the new create_namespace function
    namespace_resource = create_namespace(
        config=namespace_config,
        k8s_provider=k8s_provider,
        depends_on=depends_on,
    )

    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"

    # Handle 'latest' or None version
    if version == 'latest' or version is None:
        # Fetch the latest version from the helm chart index
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name)
        version = version.lstrip("v")
        pulumi.log.info(f"Setting helm release version to latest: {chart_name}/{version}")
    else:
        # Log the version being used
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # Generate Helm values
    helm_values = gen_helm_values(config_cert_manager)

    # Deploy cert-manager using the Helm release with custom values
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

    # Create a self-signed ClusterIssuer resource
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

    # Retrieve the CA certificate secret
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

    # Extract the tls.crt value from the secret
    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64, ca_secret

def gen_helm_values(
        config_cert_manager: CertManagerConfig
    ) -> Dict[str, Any]:
    """
    Generates custom Helm values for the cert-manager Helm chart.

    Args:
        config_cert_manager: Configuration object for Cert Manager.

    Returns:
        A dictionary of Helm values.
    """
    # Define custom values for the cert-manager Helm chart
    helm_values = {
        'replicaCount': 1,
        'installCRDs': config_cert_manager.install_crds,
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
    return helm_values
