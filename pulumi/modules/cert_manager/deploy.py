# ./pulumi/modules/cert_manager/deploy.py
# Description: Deploys the CertManager module using Helm with labels and annotations.

from typing import List, Dict, Any, Tuple, Optional  # Add Optional import
import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource

from core.namespace import create_namespace
from core.helm_chart_versions import get_latest_helm_chart_version
from core.types import NamespaceConfig
from core.metadata import get_global_annotations, get_global_labels
from .types import CertManagerConfig

def deploy_cert_manager_module(
        config_cert_manager: CertManagerConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, pulumi.Resource, str]:
    """
    Deploys the CertManager module with labels and annotations.

    Args:
        config_cert_manager (CertManagerConfig): Configuration object for CertManager deployment.
        global_depends_on (List[pulumi.Resource]): A list of resources that the deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.

    Returns:
        Tuple[str, pulumi.Resource, str]: The deployed CertManager version, release resource, and Base64-encoded CA certificate.
    """
    cert_manager_version, release, ca_cert_b64 = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    global_depends_on.append(release)

    return cert_manager_version, release, ca_cert_b64

def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider
    ) -> Tuple[str, k8s.helm.v3.Release, str]:
    """
    Deploys CertManager using Helm with labels and annotations.

    Args:
        config_cert_manager (CertManagerConfig): Configuration object for CertManager deployment.
        depends_on (List[pulumi.Resource]): List of resources that this deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.

    Returns:
        Tuple[str, k8s.helm.v3.Release, str]: The CertManager version, release resource, and Base64-encoded CA certificate.
    """
    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    namespace_config = NamespaceConfig(name=namespace)
    namespace_resource = create_namespace(namespace_config, k8s_provider, depends_on)

    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"
    version = get_helm_chart_version(chart_url, chart_name, version)

    helm_values = generate_helm_values(config_cert_manager)

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def helm_transform(args: pulumi.ResourceTransformationArgs):
        metadata = args.props.get('metadata', {})
        set_resource_metadata(metadata, get_global_labels(), get_global_annotations())
        args.props['metadata'] = metadata
        return pulumi.ResourceTransformationResult(args.props, args.opts)

    release = k8s.helm.v3.Release(
        chart_name,
        k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            namespace=namespace,
            skip_await=False,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo=chart_url),
            values=helm_values,
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace_resource,
            depends_on=[namespace_resource] + (depends_on or []),
            transformations=[helm_transform],
            custom_timeouts=pulumi.CustomTimeouts(create="8m", update="4m", delete="4m")
        )
    )

    cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer = create_cluster_issuers(
        cluster_issuer_name, namespace, k8s_provider, release
    )

    ca_secret = k8s.core.v1.Secret(
        "cluster-selfsigned-issuer-ca-secret",
        metadata={"name": "cluster-selfsigned-issuer-ca", "namespace": namespace},
        opts=pulumi.ResourceOptions(provider=k8s_provider, parent=cluster_issuer, depends_on=[cluster_issuer])
    )

    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64

def generate_helm_values(config_cert_manager: CertManagerConfig) -> Dict[str, Any]:
    """
    Generates Helm values for CertManager from the configuration object.

    Args:
        config_cert_manager (CertManagerConfig): The configuration object for CertManager.

    Returns:
        Dict[str, Any]: The Helm values dictionary for CertManager.
    """
    return {
        'replicaCount': 1,
        'installCRDs': config_cert_manager.install_crds,
        'resources': {
            'limits': {'cpu': '500m', 'memory': '1024Mi'},
            'requests': {'cpu': '250m', 'memory': '512Mi'}
        }
    }

def get_helm_chart_version(chart_url: str, chart_name: str, version: Optional[str]) -> str:
    """
    Fetches or verifies the Helm chart version.

    Args:
        chart_url (str): The Helm chart repository URL.
        chart_name (str): The name of the Helm chart.
        version (Optional[str]): The specified version or 'latest'.

    Returns:
        str: The resolved version of the Helm chart.
    """
    if version == 'latest' or version is None:
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name).lstrip("v")
        pulumi.log.info(f"Setting Helm release version to latest: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using Helm release version: {chart_name}/{version}")
    return version

def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    """
    Sets metadata for a resource with global labels and annotations.

    Args:
        metadata: The metadata object or dictionary.
        global_labels (Dict[str, str]): The global labels.
        global_annotations (Dict[str, str]): The global annotations.
    """
    if isinstance(metadata, dict):
        if metadata.get('labels') is None:
            metadata['labels'] = {}
        metadata.setdefault('labels', {}).update(global_labels)

        if metadata.get('annotations') is None:
            metadata['annotations'] = {}
        metadata.setdefault('annotations', {}).update(global_annotations)

    elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
        if metadata.labels is None:
            metadata.labels = {}
        metadata.labels.update(global_labels)

        if metadata.annotations is None:
            metadata.annotations = {}
        metadata.annotations.update(global_annotations)

def create_cluster_issuers(cluster_issuer_name: str, namespace: str, k8s_provider: k8s.Provider, release: pulumi.Resource) -> Tuple[CustomResource, CustomResource, CustomResource]:
    """
    Creates cluster issuers for cert-manager.

    Args:
        cluster_issuer_name (str): The name of the cluster issuer.
        namespace (str): The namespace for the cluster issuer.
        k8s_provider (k8s.Provider): The Kubernetes provider.
        release (pulumi.Resource): The release resource.

    Returns:
        Tuple[CustomResource, CustomResource, CustomResource]: The created cluster issuers.
    """
    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={"name": "cluster-selfsigned-issuer-root"},
        spec={"selfSigned": {}},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, parent=release, depends_on=[release],
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m")
        )
    )

    cluster_issuer_ca_certificate = CustomResource(
        "cluster-selfsigned-issuer-ca",
        api_version="cert-manager.io/v1",
        kind="Certificate",
        metadata={"name": "cluster-selfsigned-issuer-ca", "namespace": namespace},
        spec={
            "commonName": "cluster-selfsigned-issuer-ca",
            "duration": "2160h0m0s",
            "isCA": True,
            "issuerRef": {"group": "cert-manager.io", "kind": "ClusterIssuer", "name": "cluster-selfsigned-issuer-root"},
            "privateKey": {"algorithm": "ECDSA", "size": 256},
            "renewBefore": "360h0m0s",
            "secretName": "cluster-selfsigned-issuer-ca"
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, parent=cluster_issuer_root, depends_on=[cluster_issuer_root],
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m")
        )
    )

    cluster_issuer = CustomResource(
        cluster_issuer_name,
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={"name": cluster_issuer_name},
        spec={"ca": {"secretName": "cluster-selfsigned-issuer-ca"}},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider, parent=cluster_issuer_ca_certificate, depends_on=[cluster_issuer_ca_certificate],
            custom_timeouts=pulumi.CustomTimeouts(create="4m", update="4m", delete="4m")
        )
    )

    return cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer
