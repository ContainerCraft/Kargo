import pulumi
from pulumi_kubernetes import helm, Provider

import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from ...lib.helm_chart_versions import get_latest_helm_chart_version
import json
import secrets
import base64
from kubernetes import config, dynamic
from kubernetes import client as k8s_client
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from kubernetes.client import api_client


def deploy(name: str, k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str):
    # Initialize Pulumi configuration
    pconfig = pulumi.Config()

    # Deploy the Kubernetes Dashboard 6.0.8
    k8s_db_release = deploy_kubernetes_dashboard(name=name,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace)

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
    domain_suffix = pconfig.require('openunison.dns_suffix')

    # get the cluster issuer
    cluster_issuer = pconfig.require('openunison.cluster_issuer')

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

    # this is probably the wrong way to do this, but <shrug>
    config.load_kube_config()


    cluster_issuer_object = k8s_client.CustomObjectsApi().get_cluster_custom_object(group="cert-manager.io",version="v1",plural="clusterissuers",name=cluster_issuer)

    cluster_issuer_ca_secret_name = cluster_issuer_object["spec"]["ca"]["secretName"]

    pulumi.log.info("Loading CA from {}".format(cluster_issuer_ca_secret_name))

    ca_secret = k8s_client.CoreV1Api().read_namespaced_secret(namespace="cert-manager",name=cluster_issuer_ca_secret_name)

    ca_cert = ca_secret.data["tls.crt"]

    pulumi.log.info("CA Certificate {}".format(ca_cert))

    deploy_openunison_charts(ca_cert=ca_cert,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace,domain_suffix=domain_suffix,openunison_certificate=openunison_certificate,config=pconfig,db_release=k8s_db_release)


    # get the cluster issuer
    # cluster_issuer = CustomResource.get(resource_name="openunison_cluster_issuer",id=cluster_issuer,api_version="cert-manager.io/v1",kind="ClusterIssuer",opts=pulumi.ResourceOptions(
    #                                                 provider = k8s_provider,
    #                                                 depends_on=[],
    #                                                 custom_timeouts=pulumi.CustomTimeouts(
    #                                                     create="5m",
    #                                                     update="10m",
    #                                                     delete="10m"
    #                                                 )
    #                                             ))

    # pulumi.export("openunison_cluster_issuer",cluster_issuer)

    # # get the CA certificate from the issued cert
    # cert_ca = k8s.core.v1.Secret.get("ou-tls-certificate",cluster_issuer.spec.ca.secretName.apply(lambda secretName: "cert-manager/" + secretName),
    #                                         opts=pulumi.ResourceOptions(
    #                                             provider = k8s_provider,
    #                                             depends_on=[],
    #                                             custom_timeouts=pulumi.CustomTimeouts(
    #                                                 create="5m",
    #                                                 update="10m",
    #                                                 delete="10m"
    #                                             )
    #                                         )).data["tls.crt"].apply(lambda data: data  )



    # deploy_openunison_charts(ca_cert=cert_ca,k8s_provider=k8s_provider,kubernetes_distribution=kubernetes_distribution,project_name=project_name,namespace=namespace,domain_suffix=domain_suffix,openunison_certificate=openunison_certificate,config=pconfig,db_release=k8s_db_release)


def deploy_openunison_charts(ca_cert,k8s_provider: Provider, kubernetes_distribution: str, project_name: str, namespace: str,domain_suffix: str,openunison_certificate,config,db_release):
    openunison_helm_values = {  "enable_wait_for_job": True,
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
                                    "label": "app.kubernetes.io/name=kubernetes-dashboard",
                                    #"service_name": db_release.name.apply(lambda name: "kubernetes-dashboard-" + name)   ,
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
                                    "client_id": config.require('openunison.github.client_id'),
                                    "teams": config.require('openunison.github.teams'),
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

    # Fetch the latest version from the helm chart index
    chart_name = "openunison-operator"
    chart_index_path = "index.yaml"
    chart_url = "https://nexus.tremolo.io/repository/helm"
    index_url = f"{chart_url}/{chart_index_path}"
    chart_version = get_latest_helm_chart_version(index_url,chart_name)

    openunison_operator_release = k8s.helm.v3.Release(
            'openunison-operator',
            k8s.helm.v3.ReleaseArgs(
                chart=chart_name,
                version=chart_version,
                values=openunison_helm_values,
                namespace='openunison',
                skip_await=False,
                repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                    repo=chart_url
                ),
            ),
            opts=pulumi.ResourceOptions(
                provider = k8s_provider,
                depends_on=[openunison_certificate],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="8m",
                    update="10m",
                    delete="10m"
                )
            )
        )

    raw_secret_data = {
        "K8S_DB_SECRET": secrets.token_urlsafe(64),
        "unisonKeystorePassword": secrets.token_urlsafe(64),

    }
    encoded_secret_data = {key: base64.b64encode(value.encode('utf-8')).decode('utf-8')
                           for key, value in raw_secret_data.items()}

    orchestra_secret_source = k8s.core.v1.Secret("orchestra-secrets-source",
                metadata= k8s.meta.v1.ObjectMetaArgs(
                    name="orchestra-secrets-source",
                    namespace="openunison"
                ),
                data={
                    "K8S_DB_SECRET": encoded_secret_data['K8S_DB_SECRET'],
                    "unisonKeystorePassword": encoded_secret_data["unisonKeystorePassword"],
                    "GITHUB_SECRET_ID": config.require_secret('openunison.github.client_secret').apply(lambda client_secret : base64.b64encode(client_secret.encode('utf-8')).decode('utf-8') ),
                },
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

    orchestra_chart_name = 'orchestra'
    orchestra_chart_version = get_latest_helm_chart_version(index_url,orchestra_chart_name)
    openunison_orchestra_release = k8s.helm.v3.Release(
                'orchestra',
                k8s.helm.v3.ReleaseArgs(
                    chart=orchestra_chart_name,
                    version=orchestra_chart_version,
                    values=openunison_helm_values,
                    namespace='openunison',
                    skip_await=False,
                    wait_for_jobs=True,
                    repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                        repo=chart_url
                    ),

                ),

                opts=pulumi.ResourceOptions(
                    provider = k8s_provider,
                    depends_on=[openunison_operator_release,orchestra_secret_source],
                    custom_timeouts=pulumi.CustomTimeouts(
                        create="8m",
                        update="10m",
                        delete="10m"
                    )
                )
            )

    pulumi.export("openunison_orchestra_release",openunison_orchestra_release)

    openunison_helm_values["impersonation"]["orchestra_release_name"] = openunison_orchestra_release.name.apply(lambda name: name)

    orchestra_login_portal_chart_name = 'orchestra-login-portal'
    orchestra_login_portal_chart_version = get_latest_helm_chart_version(index_url,orchestra_login_portal_chart_name)
    openunison_orchestra_login_portal_release = k8s.helm.v3.Release(
                'orchestra-login-portal',
                k8s.helm.v3.ReleaseArgs(
                    chart=orchestra_login_portal_chart_name,
                    version=orchestra_login_portal_chart_version,
                    values=openunison_helm_values,
                    namespace='openunison',
                    skip_await=False,
                    wait_for_jobs=True,
                    repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                        repo=chart_url
                    ),

                ),

                opts=pulumi.ResourceOptions(
                    provider = k8s_provider,
                    depends_on=[openunison_orchestra_release],
                    custom_timeouts=pulumi.CustomTimeouts(
                        create="8m",
                        update="10m",
                        delete="10m"
                    )
                )
            )

    orchestra_kube_oidc_proxy_chart_name = 'orchestra-kube-oidc-proxy'
    orchestra_kube_oidc_proxy_chart_version = get_latest_helm_chart_version(index_url,orchestra_kube_oidc_proxy_chart_name)
    openunison_kube_oidc_proxy_release = k8s.helm.v3.Release(
                'orchestra-kube-oidc-proxy',
                k8s.helm.v3.ReleaseArgs(
                    chart=orchestra_kube_oidc_proxy_chart_name,
                    version=orchestra_kube_oidc_proxy_chart_version,
                    values=openunison_helm_values,
                    namespace='openunison',
                    skip_await=False,
                    wait_for_jobs=True,
                    repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                        repo=chart_url
                    ),

                ),

                opts=pulumi.ResourceOptions(
                    provider = k8s_provider,
                    depends_on=[openunison_orchestra_login_portal_release],
                    custom_timeouts=pulumi.CustomTimeouts(
                        create="8m",
                        update="10m",
                        delete="10m"
                    )
                )
            )







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

    k8s_db_release = k8s.helm.v3.Release(
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

    return k8s_db_release
