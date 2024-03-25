import os
import pulumi
import pulumi_kubernetes as k8s

def deploy_cluster_network_addons(k8s_provider: k8s.Provider):
    # Kubernetes YAML manifest URLs
    manifest_urls = [
        "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/v0.90.1/namespace.yaml",
        "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/v0.90.1/network-addons-config.crd.yaml",
        "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/v0.90.1/operator.yaml",
    ]

    resources = []

    for i, url in enumerate(manifest_urls):
        file_name = os.path.splitext(os.path.basename(url))[0]
        resource_name = f"nado-{file_name}"
        resource = k8s.yaml.ConfigFile(
            resource_name,
            file=url
        )
        resources.append(resource)

    network_addons_config = k8s.apiextensions.CustomResource(
        "network-addons-config",
        api_version="networkaddonsoperator.network.kubevirt.io/v1",
        kind="NetworkAddonsConfig",
        metadata={
            "name": "cluster",
        },
        spec={
            #"multus": {},
            #"multusDynamicNetworks": {},
            #"kubeSecondaryDNS": {},
            #"linuxBridge": {},
            #"kubeMacPool": {},
            #"macvtap": {},
            #"ovs": {},
            "imagePullPolicy": "IfNotPresent",
            "selfSignConfiguration": {
                "caRotateInterval": "168h",
                "caOverlapInterval": "24h",
                "certRotateInterval": "24h",
                "certOverlapInterval": "8h",
            }
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
        }
    )

    # Variable settings for the name and bridge configuration
    network_name = "br0"
    bridge_name = "br0"

    # Pulumi Kubernetes resource for NetworkAttachmentDefinition
    network_attachment_definition = k8s.apiextensions.CustomResource(
        "kargo-net-attach-def",
        api_version="k8s.cni.cncf.io/v1",
        kind="NetworkAttachmentDefinition",
        metadata={
            "name": f"{network_name}",
            "namespace": "default"
        },
        spec={
            "config": pulumi.Output.all(network_name, bridge_name).apply(lambda args: f'''
            {{
                "cniVersion": "0.3.1",
                "name": "{args[0]}",
                "plugins": [
                    {{
                        "type": "bridge",
                        "bridge": "{args[1]}",
                        "ipam": {{}}
                    }},
                    {{
                        "type": "tuning"
                    }}
                ]
            }}''')
        }
    )

    # Export the name of the resource
    pulumi.export('network_attachment_definition_name', network_attachment_definition.metadata['name'])
