import json
import os
import base64
import secrets
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource
from src.lib.namespace import create_namespace
from src.lib.helm_chart_versions import get_latest_helm_chart_version

def sanitize_name(name: str) -> str:
    """Ensure the name complies with DNS-1035 and RFC 1123."""
    name = name.strip('-')
    if not name:
        raise ValueError("Invalid name: resulting sanitized name is empty")
    return name

def deploy_openunison(
        depends,
        ns_name: str,
        version: str,
        k8s_provider: k8s.Provider,
        domain_suffix: str,
        cluster_issuer: str,
        cert_manager_selfsigned_cert: str,
        ou_github_client_id: str,
        ou_github_client_secret: str,
        ou_github_teams: str,
        enabled
    ):
    kubernetes_dashboard_release = enabled["kubernetes_dashboard"]["release"]
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubernetes.io/metadata.name": ns_name
    }
    namespace = create_namespace(
        None,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        ns_labels,
        ns_annotations
    )

    ou_certificate = CustomResource(
        "ou-tls-certificate",
        api_version="cert-manager.io/v1",
        kind="Certificate",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ou-tls-certificate",
            namespace=ns_name,
        ),
        spec={
            "secretName": "ou-tls-certificate",
            "commonName": domain_suffix,
            "isCA": False,
            "dnsNames": [
                domain_suffix,
                f"*.{domain_suffix}"
            ],
            "issuerRef": {
                "name": cluster_issuer,
                "kind": "ClusterIssuer",
                "group": "cert-manager.io",
            },
            "privateKey": {
                "algorithm": "RSA",
                "encoding": "PKCS1",
                "size": 2048,
            },
            "usages": [
                "server auth",
                "client auth"
            ]
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=depends,
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )
    depends.append(ou_certificate)

    ou_host = ""
    k8sdb_host = ""
    api_server_host = ""
    kubevirt_manager_host = ""

    running_in_gh_spaces = os.getenv("GITHUB_USER") or None

    # if running inside of Github Spaces, we'll set the hosts based on the github space name
    # if it's standalone, we'll configure based on the suffix
    if running_in_gh_spaces:
        ou_host = os.getenv("CODESPACE_NAME") + '-10443.app.github.dev'
        k8sdb_host = os.getenv("CODESPACE_NAME") + '-11443.app.github.dev'
        api_server_host = os.getenv("CODESPACE_NAME") + '-12443.app.github.dev'
        kubevirt_manager_host = os.getenv("CODESPACE_NAME") + '-13443.app.github.dev'
    else:
        ou_host = f"k8sou.{domain_suffix}"
        k8sdb_host = f"k8sdb.{domain_suffix}"
        api_server_host = f"k8sapi.{domain_suffix}"
        kubevirt_manager_host = f"kubevirt-manager.{domain_suffix}"

    ou_helm_values = {
        "enable_wait_for_job": True,
        "network": {
            "openunison_host": ou_host,
            "dashboard_host": k8sdb_host,
            "api_server_host": api_server_host,
            "session_inactivity_timeout_seconds": 900,
            "k8s_url": "https://192.168.2.130:6443",
            "force_redirect_to_tls": False,
            "createIngressCertificate": False,
            "ingress_type": "nginx",
            "ingress_annotations": {}
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
            "use_jetstack": not running_in_gh_spaces,
            "explicit_certificate_trust": not running_in_gh_spaces
        },
        "dashboard": {
            "namespace": "kubernetes-dashboard",
            "label": "k8s-app=kubernetes-dashboard",
            "require_session": True,
            "new": True

        },
        "certs": {
            "use_k8s_cm": False
        },
        "trusted_certs": [

        ],
        "monitoring": {
            "prometheus_service_account": "system:serviceaccount:monitoring:prometheus-k8s"
        },
        "github": {
            "client_id": ou_github_client_id,
            "teams": ou_github_teams,
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
            "node_selectors": []
        },
        "openunison": {
        "replicas": 1,
        "non_secret_data": {
            "K8S_DB_SSO": "oidc",
            "PROMETHEUS_SERVICE_ACCOUNT": "system:serviceaccount:monitoring:prometheus-k8s",
            "SHOW_PORTAL_ORGS": "False"
        },
        "secrets": [],
        "enable_provisioning": False,
        "use_standard_jit_workflow": True,
        "apps":[],
        }
    }

    if not running_in_gh_spaces:
        ou_helm_values["trusted_certs"].append(
            {
            "name": "unison-ca",
            "pem_b64": cert_manager_selfsigned_cert,
            }
        )

    # now that OpenUnison is deployed, we'll make ClusterAdmins of all the groups specified in openunison.github.teams
    github_teams = ou_github_teams.split(',')
    subjects = []
    az_groups = []
    for team in github_teams:
        team = team.strip()
        if team.endswith('/'):
            team = team[:-1]

        team = sanitize_name(team)

        subject = k8s.rbac.v1.SubjectArgs(
            kind="Group",
            api_group="rbac.authorization.k8s.io",
            name=team
        )
        subjects.append(subject)
        az_groups.append(team)

    # Retrieve encoded icon assets
    from src.openunison.encoded_assets import return_encoded_assets
    assets = return_encoded_assets()

    # Define the icons for the apps as json serializable base64 encoded strings
    kubevirt_icon_json = json.dumps(assets["kubevirt_icon"])
    prometheus_icon_json = json.dumps(assets["prometheus_icon"])
    alertmanager_icon_json = json.dumps(assets["alertmanager_icon"])
    grafana_icon_json = json.dumps(assets["grafana_icon"])



    # if enabled["kubevirt"] and enabled["kubevirt"]["enabled"]:
    if "kubevirt_manager" in enabled and  enabled["kubevirt_manager"]["enabled"]:
        ou_helm_values["openunison"]["apps"].append(
            {
                "name": "kubevirt-manager",
                "label": "KubeVirt Manager",
                "org": "b1bf4c92-7220-4ad2-91af-ee0fe0af7312",
                "badgeUrl": "https://" + kubevirt_manager_host,
                "injectToken": False,
                "proxyTo": "http://kubevirt-manager.kubevirt-manager.svc:8080${fullURI}",
                "az_groups": az_groups,
                "icon": f"{kubevirt_icon_json}",
            }
        )

    # if enabled["prometheus"] and enabled["prometheus"]["enabled"]:
    #     ou_helm_values["openunison"]["apps"].append(
    #         {
    #             "name": "prometheus",
    #             "label": "Prometheus",
    #             "org": "b1bf4c92-7220-4ad2-91af-ee0fe0af7312",
    #             "badgeUrl": f"https://prometheus.{domain_suffix}/",
    #             "injectToken": False,
    #             "proxyTo": "http://prometheus.monitoring.svc:9090${fullURI}",
    #             "az_groups": az_groups,
    #             "icon": f"{prometheus_icon_json}",
    #         }
    #     )

    #     ou_helm_values["openunison"]["apps"].append(
    #                 {
    #                     "name": "alertmanager",
    #                     "label": "Alert Manager",
    #                     "org": "b1bf4c92-7220-4ad2-91af-ee0fe0af7312",
    #                     "badgeUrl": "https://alertmanager." + domain_suffix + "/",
    #                     "injectToken": False,
    #                     "proxyTo": "http://alertmanager.monitoring.svc:9093${fullURI}",
    #                     "az_groups": az_groups,
    #                     "icon": f"{alertmanager_icon_json}",
    #                 }
    #     )

    #     ou_helm_values["openunison"]["apps"].append(
    #         {
    #             "name": "grafana",
    #             "label": "Grafana",
    #             "org": "b1bf4c92-7220-4ad2-91af-ee0fe0af7312",
    #             "badgeUrl": "https://grafana." + domain_suffix + "/",
    #             "injectToken": False,
    #             "azSuccessResponse":"grafana",
    #             "proxyTo": "http://grafana.monitoring.svc${fullURI}",
    #             "az_groups": az_groups,
    #             "icon": f"{grafana_icon_json}",
    #         }
    #     )

    ou_helm_values["dashboard"]["service_name"] = kubernetes_dashboard_release.name.apply(lambda name: sanitize_name(name))
    ou_helm_values["dashboard"]["auth_service_name"] = kubernetes_dashboard_release.name.apply(lambda name: sanitize_name(name + '-auth'))
    ou_helm_values["dashboard"]["api_service_name"] = kubernetes_dashboard_release.name.apply(lambda name: sanitize_name(name + '-api'))
    ou_helm_values["dashboard"]["web_service_name"] = kubernetes_dashboard_release.name.apply(lambda name: sanitize_name(name + '-web'))


    # Apply function to wait for the dashboard release names before proceeding
    def wait_for_dashboard_release_names():
        return ou_helm_values


    orchesrta_login_portal_helm_values = kubernetes_dashboard_release.name.apply(lambda _: wait_for_dashboard_release_names())

    # Fetch the latest version from the helm chart index
    chart_name = "openunison-operator"
    chart_index_path = "index.yaml"
    chart_url = "https://nexus.tremolo.io/repository/helm"
    chart_index_url = f"{chart_url}/{chart_index_path}"
    if version is None:
        version = get_latest_helm_chart_version(chart_index_url, chart_name)
        pulumi.log.info(f"Setting helm release version to latest: {chart_name}/{version}")
    else:
        pulumi.log.info(f"Using helm release version: {chart_name}/{version}")

    # Create Helm release
    operator_release = k8s.helm.v3.Release(
        'openunison-operator',
        k8s.helm.v3.ReleaseArgs(
            chart=chart_name,
            version=version,
            values=orchesrta_login_portal_helm_values,
            namespace=ns_name,
            skip_await=False,
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=depends,
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
        "GITHUB_SECRET_ID": ou_github_client_secret
    }

    encoded_secret_data = {
        key: base64.b64encode(value.encode('utf-8')).decode('utf-8')
            for key, value in raw_secret_data.items()
    }

    # Base64 encode the GitHub client secret
    orchestra_secret_source = k8s.core.v1.Secret(
        "orchestra-secrets-source",
        metadata= k8s.meta.v1.ObjectMetaArgs(
            name="orchestra-secrets-source",
            namespace=ns_name
        ),
        data={
            "K8S_DB_SECRET": encoded_secret_data['K8S_DB_SECRET'],
            "unisonKeystorePassword": encoded_secret_data["unisonKeystorePassword"],
            "GITHUB_SECRET_ID": encoded_secret_data["GITHUB_SECRET_ID"]
        },
        opts=pulumi.ResourceOptions(
            parent=operator_release,
            provider = k8s_provider,
            retain_on_delete=False,
            delete_before_replace=True,
            custom_timeouts=pulumi.CustomTimeouts(
                create="10m",
                update="10m",
                delete="10m"
            )
        )
    )

    orchestra_chart_name = 'orchestra'
    orchestra_chart_version = get_latest_helm_chart_version(chart_index_url, orchestra_chart_name)
    ou_orchestra_release = k8s.helm.v3.Release(
        'orchestra',
        k8s.helm.v3.ReleaseArgs(
            chart=orchestra_chart_name,
            version=orchestra_chart_version,
            values=ou_helm_values,
            namespace=ns_name,
            skip_await=False,
            wait_for_jobs=True,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
        ),
        opts=pulumi.ResourceOptions(
            parent=operator_release,
            depends_on=[operator_release, orchestra_secret_source],
            provider = k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )

    ou_orchestra_release_name = ou_orchestra_release.name.apply(lambda name: name)

    def update_values(name):
        return {
            **ou_helm_values,
            "impersonation": {
                **ou_helm_values["impersonation"],
                "orchestra_release_name": name
            }
        }

    # Apply the updated values
    updated_values = ou_orchestra_release_name.apply(update_values)

    orchestra_login_portal_chart_name = 'orchestra-login-portal'
    orchestra_login_portal_chart_version = get_latest_helm_chart_version(chart_index_url,orchestra_login_portal_chart_name)
    ou_orchestra_login_portal_release = k8s.helm.v3.Release(
        'orchestra-login-portal',
        k8s.helm.v3.ReleaseArgs(
            chart=orchestra_login_portal_chart_name,
            version=orchestra_login_portal_chart_version,
            values=updated_values,
            namespace=ns_name,
            skip_await=False,
            wait_for_jobs=True,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=ou_orchestra_release,
            depends_on=[ou_orchestra_release],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )

    # Sanitize name for proxy
    proxy_name = sanitize_name('proxy')

    orchestra_kube_oidc_proxy_chart_name = 'orchestra-kube-oidc-proxy'
    orchestra_kube_oidc_proxy_chart_version = get_latest_helm_chart_version(chart_index_url, orchestra_kube_oidc_proxy_chart_name)

    ou_kube_oidc_proxy_release = k8s.helm.v3.Release(
        proxy_name,
        k8s.helm.v3.ReleaseArgs(
            chart=orchestra_kube_oidc_proxy_chart_name,
            namespace=ns_name,
            values=orchesrta_login_portal_helm_values,
            version=orchestra_kube_oidc_proxy_chart_version,
            skip_await=False,
            wait_for_jobs=True,
            repository_opts= k8s.helm.v3.RepositoryOptsArgs(
                repo=chart_url
            ),
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            parent=ou_orchestra_login_portal_release,
            depends_on=[ou_orchestra_login_portal_release],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )

    deploy_kargo_helm(running_in_gh_spaces=running_in_gh_spaces,ou_orchestra_release=ou_orchestra_release,k8s_provider=k8s_provider)
    cluster_admin_cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
        "clusteradmin-clusterrolebinding",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="openunison-github-cluster-admins"
        ),
        role_ref=k8s.rbac.v1.RoleRefArgs(
            api_group="rbac.authorization.k8s.io",  # The API group of the role being referenced
            kind="ClusterRole",  # Indicates the kind of role being referenced
            name="cluster-admin"  # The name of the ClusterRole you're binding
        ),
        subjects=subjects,
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )
    return version, operator_release
#
#
#    if prometheus_enabled:
#        # create the Grafana ResultGroup
#        ou_grafana_resultgroup = CustomResource(
#            "openunison-grafana",
#            api_version="openunison.tremolo.io/v1",
#            kind="ResultGroup",
#            metadata={
#                "labels": {
#                    "app.kubernetes.io/component": "openunison-resultgroups",
#                    "app.kubernetes.io/instance": "openunison-orchestra-login-portal",
#                    "app.kubernetes.io/name": "openunison",
#                    "app.kubernetes.io/part-of": "openunison"
#                    },
#                "name": "grafana",
#                "namespace": "openunison"
#            },
#            spec=[
#                {
#                "resultType": "header",
#                "source": "static",
#                "value": "X-WEBAUTH-GROUPS=Admin"
#                },
#                {
#                "resultType": "header",
#                "source": "user",
#                "value": "X-WEBAUTH-USER=uid"
#                }
#            ],
#            opts=pulumi.ResourceOptions(
#                provider = k8s_provider,
#                depends_on=[ou_orchestra_release],
#                custom_timeouts=pulumi.CustomTimeouts(
#                    create="5m",
#                    update="10m",
#                    delete="10m"
#                )
#            )
#        )



def deploy_kargo_helm(running_in_gh_spaces: bool,ou_orchestra_release,k8s_provider: k8s.Provider):
    kargo_values = {
        "in_github_codespace": running_in_gh_spaces,
        "orchestra_service_name": ou_orchestra_release.name.apply(lambda name: sanitize_name('openunison-' + name))
    }

    chart_name = "kargo-openunison"
    kargo_openunison_release = k8s.helm.v3.Release(
        'kargo-openunison',
        k8s.helm.v3.ReleaseArgs(
            chart='src/helm/openunison-kargo',

            namespace='openunison',
            skip_await=False,

            values=kargo_values,
        ),
        opts=pulumi.ResourceOptions(
            provider = k8s_provider,
            depends_on=[ou_orchestra_release],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="10m",
                delete="10m"
            )
        )
    )
