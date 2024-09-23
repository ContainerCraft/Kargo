# pulumi/modules/multus/deploy.py

"""
Deploys the Multus module.
"""

from typing import List, Dict, Any, Tuple, Optional
import pulumi
import pulumi_kubernetes as k8s
from core.metadata import get_global_labels, get_global_annotations
from core.resource_helpers import create_namespace, create_custom_resource
from core.utils import get_latest_helm_chart_version
from .types import MultusConfig

def deploy_multus_module(
        config_multus: MultusConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, Optional[pulumi.Resource]]:
    """
    Deploys the Multus module and returns the version and the deployed resource.
    """
    multus_version, multus_resource = deploy_multus(
        config_multus=config_multus,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Update global dependencies
    global_depends_on.append(multus_resource)

    return multus_version, multus_resource

def deploy_multus(
        config_multus: MultusConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, Optional[pulumi.Resource]]:
    """
    Deploys Multus using YAML manifest and creates a NetworkAttachmentDefinition,
    ensuring proper paths for host mounts.
    """
    namespace_resource = create_namespace(
        name=config_multus.namespace,
        labels=config_multus.labels,
        annotations=config_multus.annotations,
        k8s_provider=k8s_provider,
        parent=k8s_provider,
    )

    # Deploy Multus DaemonSet
    resource_name = f"multus-daemonset"
    version = config_multus.version or "master"
    manifest_url = f"https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/{version}/deployments/multus-daemonset-thick.yml"

    multus = k8s.yaml.ConfigFile(
        resource_name,
        file=manifest_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace_resource,
            transformations=[transform_host_path],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m",
                update="8m",
                delete="2m"
            )
        )
    )

    # Create NetworkAttachmentDefinition
    network_attachment_definition = create_custom_resource(
        name=config_multus.bridge_name,
        args={
            "apiVersion": "k8s.cni.cncf.io/v1",
            "kind": "NetworkAttachmentDefinition",
            "metadata": {
                "name": config_multus.bridge_name,
                "namespace": config_multus.namespace,
            },
            "spec": {
                "config": pulumi.Output.all(config_multus.bridge_name, config_multus.bridge_name).apply(lambda args: f'''
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
            },
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=multus,
            depends_on=namespace_resource,
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="5m",
                delete="5m",
            ),
        ),
    )

    pulumi.export('network_attachment_definition', network_attachment_definition.metadata['name'])

    return version, multus

def transform_host_path(args: pulumi.ResourceTransformationArgs) -> pulumi.ResourceTransformationResult:
    """
    Transforms the host paths in the Multus DaemonSet.
    """
    obj = args.props

    if obj.get('kind', '') == 'DaemonSet' and obj.get('metadata', {}).get('name', '') == 'kube-multus-ds':
        containers = obj['spec']['template']['spec'].get('containers', [])
        for container in containers:
            volume_mounts = container.get('volumeMounts', [])
            for vm in volume_mounts:
                current_path = vm.get('mountPath', '').rstrip('/')
                if current_path == '/run/netns':
                    vm['mountPath'] = '/var/run/netns'

        volumes = obj['spec']['template']['spec'].get('volumes', [])
        for vol in volumes:
            if 'hostPath' in vol:
                current_path = vol['hostPath'].get('path', '').rstrip('/')
                if current_path == '/run/netns':
                    vol['hostPath']['path'] = '/var/run/netns'

    return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)
