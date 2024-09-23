# pulumi/modules/cert_manager/deploy.py

"""
Deploys the cert-manager module with proper dependency management.
"""

# Necessary imports
import logging
import pulumi
import pulumi_kubernetes as k8s
from typing import List, Dict, Any, Tuple, Optional, cast
from core.types import NamespaceConfig
from core.utils import get_latest_helm_chart_version, wait_for_crds
from core.resource_helpers import (
    create_namespace,
    create_helm_release,
    create_custom_resource,
    create_secret,
)
from .types import CertManagerConfig


def deploy_cert_manager_module(
        config_cert_manager: CertManagerConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, k8s.helm.v3.Release, str]:
    """
    Deploys the cert-manager module and returns the version, release resource, and CA certificate.
    """
    # add k8s_provider to module dependencies
    # TODO: Create module specific dependencies object to avoid blocking global resources on k8s_provider or other module specific dependencies

    # Deploy cert-manager
    cert_manager_version, release, ca_cert_b64 = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,  # Correctly pass the global dependencies
        k8s_provider=k8s_provider,
    )

    # Update global dependencies
    global_depends_on.append(release)

    return cert_manager_version, release, ca_cert_b64


def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, k8s.helm.v3.Release, str]:
    """
    Deploys cert-manager using Helm and sets up cluster issuers,
    ensuring that CRDs are available before creating custom resources.
    """
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Create Namespace using the helper function
    namespace_resource = create_namespace(
        name=namespace,
        k8s_provider=k8s_provider,
        parent=k8s_provider,
        depends_on=depends_on,
    )

    # Get Helm Chart Version
    chart_name = "cert-manager"
    chart_repo_url = "https://charts.jetstack.io"

    if version == 'latest' or version is None:
        version = get_latest_helm_chart_version(chart_repo_url, chart_name)
        pulumi.log.info(f"Setting cert-manager chart version to latest: {version}")
    else:
        pulumi.log.info(f"Using cert-manager chart version: {version}")

    # Generate Helm values
    helm_values = generate_helm_values(config_cert_manager)

    # Create Helm Release using the helper function
    release = create_helm_release(
        name=chart_name,
        args=k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            namespace=namespace,
            skip_await=False,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo=chart_repo_url),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            parent=namespace_resource,
            custom_timeouts=pulumi.CustomTimeouts(create="8m", update="4m", delete="4m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[namespace_resource] + depends_on,
    )

    # Wait for the CRDs to be registered
    crds = wait_for_crds(
        crd_names=[
            "certificaterequests.cert-manager.io",
            "certificates.cert-manager.io",
            "challenges.acme.cert-manager.io",
            "clusterissuers.cert-manager.io",
            "issuers.cert-manager.io",
            "orders.acme.cert-manager.io",
        ],
        k8s_provider=k8s_provider,
        depends_on=[release],
        parent=release
    )

    # Create Cluster Issuers using the helper function
    cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer, ca_secret = create_cluster_issuers(
        cluster_issuer_name, namespace, release, crds, k8s_provider
    )

    # Extract the CA certificate from the secret
    if ca_secret:
        ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])
    else:
        ca_data_tls_crt_b64 = "<no_value_during_dry_run>"

    return version, release, ca_data_tls_crt_b64

def create_cluster_issuers(
        cluster_issuer_name: str,
        namespace: str,
        release: k8s.helm.v3.Release,
        crds: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
) -> Tuple[
    Optional[k8s.apiextensions.CustomResource],
    Optional[k8s.apiextensions.CustomResource],
    Optional[k8s.apiextensions.CustomResource],
    Optional[k8s.core.v1.Secret],
]:
    """
    Creates cluster issuers required for cert-manager, ensuring dependencies on CRDs.

    Args:
        cluster_issuer_name (str): The name of the cluster issuer.
        namespace (str): The Kubernetes namespace.
        release (k8s.helm.v3.Release): The Helm release resource.
        crds (List[pulumi.Resource]): List of CRDs.
        k8s_provider (k8s.Provider): Kubernetes provider.

    Returns:
        Tuple containing:
            - ClusterIssuer for the self-signed root.
            - ClusterIssuer's CA certificate.
            - Primary ClusterIssuer.
            - The secret resource containing the CA certificate.
    """
    try:
        # SelfSigned Root Issuer
        cluster_issuer_root = create_custom_resource(
            name="cluster-selfsigned-issuer-root",
            args={
                "apiVersion": "cert-manager.io/v1",
                "kind": "ClusterIssuer",
                "metadata": {
                    "name": "cluster-selfsigned-issuer-root",
                },
                "spec": {"selfSigned": {}},
            },
            opts=pulumi.ResourceOptions(
                parent=release,
                provider=k8s_provider,
                depends_on=crds,
                custom_timeouts=pulumi.CustomTimeouts(create="5m", update="5m", delete="5m"),
            ),
        )

        # CA Certificate Issuer
        cluster_issuer_ca_certificate = create_custom_resource(
            name="cluster-selfsigned-issuer-ca",
            args={
                "apiVersion": "cert-manager.io/v1",
                "kind": "Certificate",
                "metadata": {
                    "name": "cluster-selfsigned-issuer-ca",
                    "namespace": namespace,
                },
                "spec": {
                    "commonName": "cluster-selfsigned-issuer-ca",
                    "duration": "2160h0m0s",
                    "isCA": True,
                    "issuerRef": {
                        "group": "cert-manager.io",
                        "kind": "ClusterIssuer",
                        "name": "cluster-selfsigned-issuer-root",
                    },
                    "privateKey": {"algorithm": "RSA", "size": 2048},
                    "renewBefore": "360h0m0s",
                    "secretName": "cluster-selfsigned-issuer-ca",
                },
            },
            opts=pulumi.ResourceOptions(
                parent=cluster_issuer_root,
                provider=k8s_provider,
                depends_on=[cluster_issuer_root],
                custom_timeouts=pulumi.CustomTimeouts(create="5m", update="5m", delete="10m"),
            ),
        )

        # Main Cluster Issuer
        cluster_issuer = create_custom_resource(
            name=cluster_issuer_name,
            args={
                "apiVersion": "cert-manager.io/v1",
                "kind": "ClusterIssuer",
                "metadata": {
                    "name": cluster_issuer_name,
                },
                "spec": {
                    "ca": {"secretName": "cluster-selfsigned-issuer-ca"},
                },
            },
            opts=pulumi.ResourceOptions(
                parent=cluster_issuer_ca_certificate,
                provider=k8s_provider,
                depends_on=[cluster_issuer_ca_certificate],
                custom_timeouts=pulumi.CustomTimeouts(create="5m", update="5m", delete="5m"),
            ),
        )

        # Fetch CA Secret if not in dry-run
        if not pulumi.runtime.is_dry_run():
            ca_secret = k8s.core.v1.Secret.get(
                resource_name="cluster-selfsigned-issuer-ca",
                id=f"{namespace}/cluster-selfsigned-issuer-ca",
                opts=pulumi.ResourceOptions(
                    parent=cluster_issuer_ca_certificate,
                    provider=k8s_provider,
                    depends_on=[cluster_issuer_ca_certificate],
                )
            )
        else:
            ca_secret = None

        return cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer, ca_secret

    except Exception as e:
        pulumi.log.error(f"Error during the creation of cluster issuers: {str(e)}")
        return None, None, None, None


def generate_helm_values(config_cert_manager: CertManagerConfig) -> Dict[str, Any]:
    """
    Generates Helm values for the CertManager deployment.
    """
    return {
        'replicaCount': 1,
        'installCRDs': config_cert_manager.install_crds,
        'resources': {
            'limits': {'cpu': '500m', 'memory': '1024Mi'},
            'requests': {'cpu': '250m', 'memory': '512Mi'},
        },
    }
