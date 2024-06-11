import os
import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from src.lib.namespace import create_namespace

def deploy_cnao(
        depends,
        version: str,
        k8s_provider: k8s.Provider
    ):

    # Create namespace
    ns_name = "cluster-network-addons"
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "openshift.io/cluster-monitoring": "true",
    }
    namespace = create_namespace(
        depends,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        custom_labels=ns_labels,
        custom_annotations=ns_annotations
    )

    # Fetch the latest stable version of CDI
    if version is None:
        tag_url = 'https://github.com/kubevirt/cluster-network-addons-operator/releases/latest'
        tag = requests.get(tag_url, allow_redirects=False).headers.get('location')
        version = tag.split('/')[-1]
        version = version.lstrip('v')
        pulumi.log.info(f"Setting helm release version to latest: cnao/{version}")
    else:
        # Log the version override
        pulumi.log.info(f"Using helm release version: cnao/{version}")

    crd_manifest_url = f"https://github.com/kubevirt/cluster-network-addons-operator/releases/download/v{version}/network-addons-config.crd.yaml"
    nado_crd_resource = k8s.yaml.ConfigFile(
        "network-addons-crds",
        file=crd_manifest_url,
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=depends,
            provider=k8s_provider,
        )
    )

    operator_manifest_url = f"https://github.com/kubevirt/cluster-network-addons-operator/releases/download/v{version}/operator.yaml"
    nado_operator_resource = k8s.yaml.ConfigFile(
        "network-addons-operator",
        file=operator_manifest_url,
        opts=pulumi.ResourceOptions(
            parent=nado_crd_resource,
            depends_on=depends,
            provider=k8s_provider,
        )
    )

    network_addons_config = CustomResource(
        "network-addons-config",
        api_version="networkaddonsoperator.network.kubevirt.io/v1",
        kind="NetworkAddonsConfig",
        metadata={
            "name": "cluster",
        },
        opts=pulumi.ResourceOptions(
            parent=nado_operator_resource,
            depends_on=depends,
            provider=k8s_provider,
        ),
        spec={
            "macvtap": {},
            "linuxBridge": {},
            "imagePullPolicy": "IfNotPresent",
            "selfSignConfiguration": {
                "caRotateInterval": "168h",
                "caOverlapInterval": "24h",
                "certRotateInterval": "24h",
                "certOverlapInterval": "8h",
            }
        }
    )
            #"multus": {},
            #"multusDynamicNetworks": {},
            #"kubeSecondaryDNS": {},
            #"kubeMacPool": {},
            #"ovs": {},
            #},
            #"placementConfiguration": {
            #    "workloads": {
            #        "nodeSelector": {
            #            "node-role.kubernetes.io/worker": "",
            #        }
            #    },
            #    "infra": {
            #        "affinity": {
            #            "nodeAffinity": {
            #                "requiredDuringSchedulingIgnoredDuringExecution": {
            #                    "nodeSelectorTerms": [{
            #                        "matchExpressions": [{
            #                            "key": "node-role.kubernetes.io/worker",
            #                            "operator": "Exists",
            #                        }]
            #                    }]
            #                }
            #            }
            #        }
            #    }
            #},

    return version, nado_operator_resource

    ## Variable settings for the name and bridge configuration
    #network_name = "br0"
    #bridge_name = "br0"

    ## Pulumi Kubernetes resource for NetworkAttachmentDefinition
    #network_attachment_definition = k8s.apiextensions.CustomResource(
    #    "kargo-net-attach-def",
    #    api_version="k8s.cni.cncf.io/v1",
    #    kind="NetworkAttachmentDefinition",
    #    metadata={
    #        "name": f"{network_name}",
    #        "namespace": "default"
    #    },
    #    spec={
    #        "config": pulumi.Output.all(network_name, bridge_name).apply(lambda args: f'''
    #        {{
    #            "cniVersion": "0.3.1",
    #            "name": "{args[0]}",
    #            "plugins": [
    #                {{
    #                    "type": "bridge",
    #                    "bridge": "{args[1]}",
    #                    "ipam": {{}}
    #                }},
    #                {{
    #                    "type": "tuning"
    #                }}
    #            ]
    #        }}''')
    #    }
    #)

    ## Export the name of the resource
    #pulumi.export('network_attachment_definition_name', network_attachment_definition.metadata['name'])
