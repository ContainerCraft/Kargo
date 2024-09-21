# pulumi/modules/cert_manager/deploy.py

"""
Deploys the CertManager module using Helm with labels and annotations.
"""

from typing import List, Dict, Any, Tuple, Optional
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource

from core.types import NamespaceConfig
from core.metadata import get_global_annotations, get_global_labels
from core.utils import set_resource_metadata, get_latest_helm_chart_version
from .types import CertManagerConfig

def deploy_cert_manager_module(
        config_cert_manager: CertManagerConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, pulumi.Resource, str]:

    cert_manager_version, release, ca_cert_b64 = deploy_cert_manager(
        config_cert_manager=config_cert_manager,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    pulumi.export("cert_manager_selfsigned_cert", ca_cert_b64)
    global_depends_on.append(release)

    return cert_manager_version, release, ca_cert_b64

def deploy_cert_manager(
        config_cert_manager: CertManagerConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, k8s.helm.v3.Release, str]:

    namespace = config_cert_manager.namespace
    version = config_cert_manager.version
    cluster_issuer_name = config_cert_manager.cluster_issuer
    install_crds = config_cert_manager.install_crds

    # Create Namespace
    namespace_resource = create_namespace(namespace, k8s_provider, depends_on)

    # Get Helm Chart Version
    chart_name = "cert-manager"
    chart_url = "https://charts.jetstack.io"
    version = get_helm_chart_version(chart_url, chart_name, version)

    helm_values = generate_helm_values(config_cert_manager)

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def helm_transform(args: pulumi.ResourceTransformationArgs):
        metadata = args.props.get('metadata', {})
        set_resource_metadata(metadata, global_labels, global_annotations)
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
            depends_on=[namespace_resource] + depends_on,
            transformations=[helm_transform],
            custom_timeouts=pulumi.CustomTimeouts(create="8m", update="4m", delete="4m"),
        ),
    )

    cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer = create_cluster_issuers(
        cluster_issuer_name, namespace, k8s_provider, release
    )

    ca_secret = k8s.core.v1.Secret(
        "cluster-selfsigned-issuer-ca-secret",
        metadata={"name": "cluster-selfsigned-issuer-ca", "namespace": namespace},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer,
            depends_on=[cluster_issuer],
        ),
    )

    ca_data_tls_crt_b64 = ca_secret.data.apply(lambda data: data["tls.crt"])

    return version, release, ca_data_tls_crt_b64

def generate_helm_values(config_cert_manager: CertManagerConfig) -> Dict[str, Any]:
    return {
        'replicaCount': 1,
        'installCRDs': config_cert_manager.install_crds,
        'resources': {
            'limits': {'cpu': '500m', 'memory': '1024Mi'},
            'requests': {'cpu': '250m', 'memory': '512Mi'},
        },
    }

def get_helm_chart_version(chart_url: str, chart_name: str, version: Optional[str]) -> str:
    if version == 'latest' or version is None:
        version = get_latest_helm_chart_version(f"{chart_url}/index.yaml", chart_name).lstrip("v")
        pulumi.log.info(f"Setting Helm release version to latest: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using Helm release version: {chart_name}/{version}")
    return version

def create_namespace(
        namespace_name: str,
        k8s_provider: k8s.Provider,
        depends_on: List[pulumi.Resource],
    ) -> k8s.core.v1.Namespace:
    """
    Creates a Kubernetes namespace with the provided configuration.
    """
    namespace_config = NamespaceConfig(name=namespace_name)
    namespace_resource = k8s.core.v1.Namespace(
        namespace_name,
        metadata={
            "name": namespace_config.name,
            "labels": namespace_config.labels,
            "annotations": namespace_config.annotations,
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            custom_timeouts=pulumi.CustomTimeouts(
                create=namespace_config.custom_timeouts.get("create", "5m"),
                update=namespace_config.custom_timeouts.get("update", "10m"),
                delete=namespace_config.custom_timeouts.get("delete", "10m"),
            ),
        ),
    )
    return namespace_resource

def create_cluster_issuers(
        cluster_issuer_name: str,
        namespace: str,
        k8s_provider: k8s.Provider,
        release: pulumi.Resource,
    ) -> Tuple[CustomResource, CustomResource, CustomResource]:

    cluster_issuer_root = CustomResource(
        "cluster-selfsigned-issuer-root",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={"name": "cluster-selfsigned-issuer-root"},
        spec={"selfSigned": {}},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=release,
            depends_on=[release],
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m"),
        ),
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
            "issuerRef": {
                "group": "cert-manager.io",
                "kind": "ClusterIssuer",
                "name": "cluster-selfsigned-issuer-root",
            },
            "privateKey": {"algorithm": "ECDSA", "size": 256},
            "renewBefore": "360h0m0s",
            "secretName": "cluster-selfsigned-issuer-ca",
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer_root,
            depends_on=[cluster_issuer_root],
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="10m", delete="10m"),
        ),
    )

    cluster_issuer = CustomResource(
        cluster_issuer_name,
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata={"name": cluster_issuer_name},
        spec={"ca": {"secretName": "cluster-selfsigned-issuer-ca"}},
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=cluster_issuer_ca_certificate,
            depends_on=[cluster_issuer_ca_certificate],
            custom_timeouts=pulumi.CustomTimeouts(create="4m", update="4m", delete="4m"),
        ),
    )

    return cluster_issuer_root, cluster_issuer_ca_certificate, cluster_issuer
