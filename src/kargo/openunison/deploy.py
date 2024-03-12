import pulumi
from pulumi_kubernetes import helm, Provider
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from ...lib.helm_chart_versions import get_latest_helm_chart_version
import json

def deploy(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    # Initialize Pulumi configuration
    config = pulumi.Config()

    # Deploy the Kubernetes Dashboard 6.0.8
    deploy_kubernetes_dashboard(name=name,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace)

    # generate openunison namespace
    openunison_namespace = k8s.core.v1.Namespace("openunison",
            metadata= k8s.meta.v1.ObjectMetaArgs(
                name="openunison"
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

    # get the domain suffix and cluster_issuer
    domain_suffix = config.require('openunison.dns_suffix')

    # get the cluster issuer
    cluster_issuer = config.require('openunison.cluster_issuer')

    # create the Certificate
    openunison_certificate = CustomResource("ou-tls-certificate",
                                            api_version="cert-manager.io/v1",
                                            kind="Certificate",
                                            metadata={
                                                "name": "ou-tls-certificate",
                                                "namespace": "openunison",
                                            },
                                            spec={
                                                "secretName": "ou-tls-certificate",
                                                "commonName": "*." + domain_suffix,
                                                "isCA": False,
                                                "privateKey": {
                                                    "algorithm": "RSA",
                                                    "encoding": "PKCS1",
                                                    "size": 2048,
                                                },
                                                "usages": ["server auth","client auth"],
                                                "dnsNames": ["*." + domain_suffix, domain_suffix],
                                                "issuerRef": {
                                                    "name": cluster_issuer,
                                                    "kind": "ClusterIssuer",
                                                    "group": "cert-manager.io",
                                                },
                                            },
                                            opts=pulumi.ResourceOptions(
                                                provider = k8s_provider,
                                                depends_on=[openunison_namespace],
                                                custom_timeouts=pulumi.CustomTimeouts(
                                                    create="5m",
                                                    update="10m",
                                                    delete="10m"
                                                )
                                            )
                                        )

    # get the CA certificate from the issued cert
    #deploy_openunison_charts(ca_cert=data,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace)
    cert_ca = k8s.core.v1.Secret.get("ou-tls-certificate","openunison/ou-tls-certificate").data["ca.crt"].apply(lambda data: str(data)  )
    deploy_openunison_charts(ca_cert=cert_ca,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace,domain_suffix=domain_suffix)


def deploy_openunison_charts(ca_cert: str,k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str,domain_suffix: str):
    openunison_helm_values = {
                                "network": {
                                    "openunison_host": "k8sou." + domain_suffix,
                                    "dashboard_host": "k8sdb." + domain_suffix,
                                    "api_server_host": "k8sapi." + domain_suffix,
                                    "session_inactivity_timeout_seconds": 900,
                                    "k8s_url": "https://192.168.2.130:6443",
                                    "force_redirect_to_tls": False,
                                    "createIngressCertificate": False,
                                    "ingress_type": "nginx",
                                    "ingress_annotations": {

                                    }
                                },
                                "cert_template": {
                                    "ou": "Kubernetes",
                                    "o": "MyOrg",
                                    "l": "My Cluster",
                                    "st": "State of Cluster",
                                    "c": "MyCountry"
                                },
                                "myvd_config_path": "WEB-INF/myvd.conf",
                                "k8s_cluster_name": "openunison-kargo",
                                "enable_impersonation": True,
                                "impersonation": {
                                    "use_jetstack": True,
                                    "explicit_certificate_trust": True
                                },
                                "dashboard": {
                                    "namespace": "kubernetes-dashboard",
                                    "cert_name": "kubernetes-dashboard-certs",
                                    "label": "k8s-app=kubernetes-dashboard",
                                    "service_name": "kubernetes-dashboard",
                                    "require_session": True
                                },
                                "certs": {
                                    "use_k8s_cm": False
                                },
                                "trusted_certs": [
                                {
                                    "name": "unison-ca",
                                    "pem_b64": ca_cert,
                                }
                                ],
                                "monitoring": {
                                    "prometheus_service_account": "system:serviceaccount:monitoring:prometheus-k8s"
                                },
                                "github": {
                                    "client_id": "1f9e4e4e1ad396cbb321",
                                    "teams": "TremoloSecurity/",
                                },
                                "network_policies": {
                                "enabled": False,
                                "ingress": {
                                    "enabled": True,
                                    "labels": {
                                    "app.kubernetes.io/name": "ingress-nginx"
                                    }
                                },
                                "monitoring": {
                                    "enabled": True,
                                    "labels": {
                                    "app.kubernetes.io/name": "monitoring"
                                    }
                                },
                                "apiserver": {
                                    "enabled": False,
                                    "labels": {
                                    "app.kubernetes.io/name": "kube-system"
                                    }
                                }
                                },
                                "services": {
                                "enable_tokenrequest": False,
                                "token_request_audience": "api",
                                "token_request_expiration_seconds": 600,
                                "node_selectors": [

                                ]
                                },
                                "openunison": {
                                "replicas": 1,
                                "non_secret_data": {
                                    "K8S_DB_SSO": "oidc",
                                    "PROMETHEUS_SERVICE_ACCOUNT": "system:serviceaccount:monitoring:prometheus-k8s",
                                    "SHOW_PORTAL_ORGS": "False"
                                },
                                "secrets": [

                                ],
                                "enable_provisioning": False,
                                "use_standard_jit_workflow": True
                                }
                            }

    pulumi.log.info("WTF:" + json.dumps(openunison_helm_values))
    return "wtf?"


def deploy_kubernetes_dashboard(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    # Deploy kubernetes-dashboard via the helm chart
    # Create a Namespace
    dashboard_namespace = k8s.core.v1.Namespace("kubernetes-dashboard",
        metadata= k8s.meta.v1.ObjectMetaArgs(
            name="kubernetes-dashboard"
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
    chart_name = "kubernetes-dashboard"
    chart_index_path = "index.yaml"
    chart_url = "https://kubernetes.github.io/dashboard"
    index_url = f"{chart_url}/{chart_index_path}"
    chart_version = "6.0.8"

    release = k8s.helm.v3.Release(
            'kubernetes-dashboard',
            k8s.helm.v3.ReleaseArgs(
                chart=chart_name,
                version=chart_version,
                namespace='kubernetes-dashboard',
                skip_await=False,
                repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                    repo=chart_url
                ),
            ),
            opts=pulumi.ResourceOptions(
                provider = k8s_provider,
                depends_on=[dashboard_namespace],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="8m",
                    update="10m",
                    delete="10m"
                )
            )
        )
