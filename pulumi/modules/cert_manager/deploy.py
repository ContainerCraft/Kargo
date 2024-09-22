# pulumi/modules/cert_manager/deploy.py

"""
Deploys the CertManager module using Helm with labels and annotations.
"""

import pulumi
import pulumi_kubernetes as k8s
from typing import List, Dict, Any, Tuple, Optional

from core.types import NamespaceConfig
from core.metadata import get_global_labels, get_global_annotations
from core.utils import get_latest_helm_chart_version
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
    ) -> Tuple[str, pulumi.Resource, str]:
    """
    Deploys the CertManager module and returns the version, release resource, and CA certificate.
    """
    # Deploy Cert Manager
    cert_manager_version, release, ca_cert_b64 = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Export the CA certificate
    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)

    # Update global dependencies
    global_depends_on.append(release)

    return cert_manager_version, release, ca_cert_b64

def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, k8s.helm.v3.Release, str]:
    """
    Deploys Cert Manager using Helm and sets up cluster issuers.
    """
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Create Namespace using the helper function
    namespace_resource = create_namespace(
        name=namespace,
        k8s_provider=k8s_provider,
        depends_on=depends_on,
    )

    # Get Helm Chart Version
    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"
    version = get_helm_chart_version(chart_url, chart_name, version)

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
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo=chart_url),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            parent=namespace_resource,
            custom_timeouts=pulumi.CustomTimeouts(create="8m", update="4m", delete="4m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[namespace_resource] + depends_on,
    )

    # Create Cluster Issuers using the helper function
    cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer = create_cluster_issuers(
        cluster_issuer_name, namespace, k8s_provider, release
    )

    # Create Secret using the helper function
    #ca_secret = k8s.core.v1.Secret.get(
    #    "cluster-selfsigned-issuer-ca-secret",
    #    id=f"{namespace}/cluster-selfsigned-issuer-ca",
    #    opts=pulumi.ResourceOptions(
    #        parent=cluster_issuer,
    #        depends_on=[cluster_issuer],
    #        provider=k8s_provider,
    #    )
    #)
    ca_secret = create_secret(
        name="cluster-selfsigned-issuer-ca-secret",
        args={
            "metadata": {
                "name": "cluster-selfsigned-issuer-ca",
                "namespace": namespace,
            },
        },
        opts=pulumi.ResourceOptions(
            parent=cluster_issuer,
            custom_timeouts=pulumi.CustomTimeouts(create="2m", update="2m", delete="2m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[cluster_issuer],
    )

    # Extract the CA certificate from the secret
    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64

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

def get_helm_chart_version(chart_url: str, chart_name: str, version: Optional[str]) -> str:
    """
    Retrieves the Helm chart version.
    """
    if version == 'latest' or version is None:
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name).lstrip("v")
        pulumi.log.info(f"Setting Helm release version to latest: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using Helm release version: {chart_name}/{version}")
    return version

def create_cluster_issuers(
        cluster_issuer_name: str,
        namespace: str,
        k8s_provider: k8s.Provider,
        release: pulumi.Resource
    ) -> Tuple[k8s.apiextensions.CustomResource, k8s.apiextensions.CustomResource, k8s.apiextensions.CustomResource]:
    """
    Creates cluster issuers required for CertManager.
    """
    # Create ClusterIssuer root using the helper function
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
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[release],
    )

    # Create ClusterIssuer CA Certificate using the helper function
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
                "privateKey": {"algorithm": "ECDSA", "size": 256},
                "renewBefore": "360h0m0s",
                "secretName": "cluster-selfsigned-issuer-ca",
            },
        },
        opts=pulumi.ResourceOptions(
            parent=cluster_issuer_root,
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[cluster_issuer_root],
    )

    # Create ClusterIssuer using the helper function
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
            custom_timeouts=pulumi.CustomTimeouts(create="4m", update="4m", delete="4m"),
        ),
        k8s_provider=k8s_provider,
        depends_on=[cluster_issuer_ca_certificate],
    )

    return cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer
