import pulumi
import pulumi_kubernetes as k8s

def deploy_multus(
        depends: pulumi.Input[list],
        version: str,
        bridge_name: str,
        k8s_provider: k8s.Provider
    ):

    resource_name = f"k8snetworkplumbingwg-multus-daemonset-thick"
    manifest_url = f"https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/{version}/deployments/multus-daemonset-thick.yml"

    multus = k8s.yaml.ConfigFile(
        resource_name,
        file=manifest_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends,
            transformations=[transform_host_path]
        )
    )

    # Pulumi Kubernetes resource for NetworkAttachmentDefinition
    network_attachment_definition = k8s.apiextensions.CustomResource(
        "kargo-net-attach-def",
        api_version="k8s.cni.cncf.io/v1",
        kind="NetworkAttachmentDefinition",
        metadata={
            "name": f"{bridge_name}",
            "namespace": "default"
        },
        spec={
            "config": pulumi.Output.all(bridge_name, bridge_name).apply(lambda args: f'''
            {{
                "cniVersion": "0.3.1",
                "name": "{bridge_name}",
                "plugins": [
                    {{
                        "type": "bridge",
                        "bridge": "{bridge_name}",
                        "ipam": {{}}
                    }},
                    {{
                        "type": "tuning"
                    }}
                ]
            }}''')
        },
        opts=pulumi.ResourceOptions(
            depends_on=depends,
            provider=k8s_provider
        )
    )

    # Export the name of the resource
    pulumi.export('network_attachment_definition', network_attachment_definition.metadata['name'])

    return "master", multus

def transform_host_path(args):

    # Get the object from the arguments
    obj = args.props
    pulumi.log.debug(f"Object keys: {list(obj.keys())}")

    # Transform DaemonSet named 'kube-multus-ds'
    if obj.get('kind', '') == 'DaemonSet' and obj.get('metadata', {}).get('name', '') == 'kube-multus-ds':
        # Ensure spec is present
        if 'spec' in obj:
            # Transform paths in containers
            containers = obj['spec']['template']['spec'].get('containers', [])
            for container in containers:
                volume_mounts = container.get('volumeMounts', [])
                for vm in volume_mounts:
                    # Normalize path before checking to handle potential trailing slash
                    current_path = vm.get('mountPath', '').rstrip('/')
                    if current_path == '/run/netns':
                        vm['mountPath'] = '/var/run/netns'

            # Transform paths in volumes
            volumes = obj['spec']['template']['spec'].get('volumes', [])
            for vol in volumes:
                if 'hostPath' in vol:
                    # Normalize path before checking to handle potential trailing slash
                    current_path = vol['hostPath'].get('path', '').rstrip('/')
                    if current_path == '/run/netns':
                        vol['hostPath']['path'] = '/var/run/netns'

    # Return the modified object
    return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)
