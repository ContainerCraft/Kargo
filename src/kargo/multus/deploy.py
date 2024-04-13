import os
import pulumi
import pulumi_kubernetes as k8s

def transform_host_path(args):
    obj = args.props
    pulumi.log.info(f"Object keys: {list(obj.keys())}")

    # Transform DaemonSet named 'kube-multus-ds'
    if obj.get('kind', '') == 'DaemonSet' and obj.get('metadata', {}).get('name', '') == 'kube-multus-ds':
        # Ensure spec is present
        if 'spec' in obj:
            # Transform paths in containers
            containers = obj['spec']['template']['spec'].get('containers', [])
            for container in containers:
                volume_mounts = container.get('volumeMounts', [])
                for vm in volume_mounts:
                    if vm.get('mountPath') == '/run/netns':
                        vm['mountPath'] = '/var/run/netns'

            # Transform paths in volumes
            volumes = obj['spec']['template']['spec'].get('volumes', [])
            for vol in volumes:
                if 'hostPath' in vol and vol['hostPath'].get('path') == '/run/netns':
                    vol['hostPath']['path'] = '/var/run/netns'

    # Return the modified object
    return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)

def deploy_multus(k8s_provider: k8s.Provider):
    resource_name = f"k8snetworkplumbingwg-multus-daemonset-thick"
    manifest_url = "https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml"
    resource = k8s.yaml.ConfigFile(
        resource_name,
        file=manifest_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            transformations=[transform_host_path]
        )
    )

    # Variable settings for the name and bridge configuration
    network_name = "lan"
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
