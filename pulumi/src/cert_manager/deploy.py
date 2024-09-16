# src/cert_manager/deploy.py

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from typing import Optional, List, Dict, Any, Tuple

from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version
from src.cert_manager.types import CertManagerConfig
from src.lib.types import NamespaceConfig
from src.lib.metadata import get_global_annotations, get_global_labels

def deploy_cert_manager_module(
        config_cert_manager: CertManagerConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, pulumi.Resource, str]:

    # Deploy cert-manager and retrieve the version, Helm release, and CA certificate
    cert_manager_version, release, ca_cert_b64 = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Append the release to global dependencies to maintain resource ordering
    global_depends_on.append(release)

    # Export the CA certificate for use by other modules or consumers
    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)

    return cert_manager_version, release, ca_cert_b64

def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: Optional[List[pulumi.Resource]],
        k8s_provider: k8s.Provider
    ) -> Tuple[str, k8s.helm.v3.Release, str]:

    # Extract configuration details
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Create the namespace for cert-manager
    namespace_config = NamespaceConfig(
        name=namespace,
    )
    namespace_resource = create_namespace(
        config=namespace_config,
        k8s_provider=k8s_provider,
        depends_on=depends_on,
    )

    # Define Helm chart details
    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"

    # Determine version
    if version == 'latest' or version is None:
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name)
        version = version.lstrip("v")
        pulumi.log.info(f"Setting Helm release version to latest: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using Helm release version: {chart_name}/{version}")

    # Generate Helm values
    helm_values = gen_helm_values(config_cert_manager)

    # Access global labels and annotations
    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    # Define transformation for Helm resources
    def helm_transform(args: pulumi.ResourceTransformationArgs):
        if args.resource and args.resource.__class__.__name__.startswith("k8s"):
            props = args.props
            if 'metadata' in props:
                metadata = props['metadata']
                if isinstance(metadata, dict):
                    metadata.setdefault('labels', {})
                    metadata['labels'].update(global_labels)
                    metadata.setdefault('annotations', {})
                    metadata['annotations'].update(global_annotations)
                elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
                    if metadata.labels is None:
                        metadata.labels = {}
                    metadata.labels = {**metadata.labels, **global_labels}
                    if metadata.annotations is None:
                        metadata.annotations = {}
                    metadata.annotations = {**metadata.annotations, **global_annotations}
                    props['metadata'] = metadata
            else:
                props['metadata'] = {
                    'labels': global_labels,
                    'annotations': global_annotations
                }
            return pulumi.ResourceTransformationResult(props, args.opts)
        return None

    # Deploy cert-manager using Helm
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
            depends_on=[namespace_resource] + (depends_on or []),
            transformations=[helm_transform],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="4m",
                delete="4m"
            )
        )
    )

    # Create ClusterIssuer resources
    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={
            "name": "cluster-selfsigned-issuer-root",
        },
        spec={
            "selfSigned": {}
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=release,
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
            "namespace": namespace,
        },
        spec={
            "commonName": "cluster-selfsigned-issuer-ca",
            "duration": "2160h0m0s",
            "isCA": True,
            "issuerRef": {
                "group": "cert-manager.io",
                "kind": "ClusterIssuer",
                "name": "cluster-selfsigned-issuer-root",
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
            depends_on=[cluster_issuer_root],
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
        },
        spec={
            "ca": {
                "secretName": "cluster-selfsigned-issuer-ca",
            }
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer_ca_certificate,
            depends_on=[cluster_issuer_ca_certificate],
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
            "name": "cluster-selfsigned-issuer-ca",
            "namespace": namespace,
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer,
            depends_on=[cluster_issuer],
        )
    )

    # Extract the base64-encoded CA certificate
    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64

def gen_helm_values(
        config_cert_manager: CertManagerConfig
    ) -> Dict[str, Any]:
    """
    Generates custom Helm values for the cert-manager Helm chart.

    Args:
        config_cert_manager (CertManagerConfig): The configuration for cert-manager.

    Returns:
        Dict[str, Any]: A dictionary of Helm chart values.
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
