# pulumi/modules/kubevirt/deploy.py

"""
Deploys the KubeVirt module.
"""

import requests
import yaml
import tempfile
import os
from typing import Optional, List, Tuple, Dict, Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from core.types import NamespaceConfig
from core.metadata import get_global_labels, get_global_annotations
from core.utils import set_resource_metadata
from .types import KubeVirtConfig

def deploy_kubevirt_module(
        config_kubevirt: KubeVirtConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:

    namespace_resource = create_namespace(
        config_kubevirt.namespace,
        k8s_provider,
        global_depends_on,
    )

    # Combine dependencies
    depends_on = global_depends_on + [namespace_resource]

    kubevirt_version, kubevirt_resource = deploy_kubevirt(
        config_kubevirt=config_kubevirt,
        depends_on=depends_on,
        k8s_provider=k8s_provider,
    )

    global_depends_on.append(kubevirt_resource)

    return kubevirt_version, kubevirt_resource

def deploy_kubevirt(
        config_kubevirt: KubeVirtConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, pulumi.Resource]:

    namespace = config_kubevirt.namespace
    version = config_kubevirt.version
    use_emulation = config_kubevirt.use_emulation
    labels = config_kubevirt.labels
    annotations = config_kubevirt.annotations

    if version == 'latest' or version is None:
        version = get_latest_kubevirt_version()
        pulumi.log.info(f"Setting KubeVirt release version to latest: {version}")
    else:
        pulumi.log.info(f"Using KubeVirt version: {version}")

    kubevirt_operator_yaml = download_kubevirt_operator_yaml(version)

    transformed_yaml = _transform_yaml(kubevirt_operator_yaml, namespace)

    def kubevirt_transform(obj: Dict[str, Any], opts: pulumi.ResourceOptions) -> pulumi.ResourceTransformationResult:
        obj.setdefault("metadata", {})
        set_resource_metadata(obj["metadata"], labels, annotations)
        if "spec" in obj and "template" in obj["spec"]:
            template_meta = obj["spec"]["template"].setdefault("metadata", {})
            set_resource_metadata(template_meta, labels, annotations)
        return pulumi.ResourceTransformationResult(obj, opts)

    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    try:
        operator = k8s.yaml.ConfigFile(
            'kubevirt-operator',
            file=temp_file_path,
            transformations=[kubevirt_transform],
            opts=pulumi.ResourceOptions(
                provider=k8s_provider,
                depends_on=depends_on,
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="5m",
                    delete="5m",
                ),
            ),
        )
    finally:
        os.unlink(temp_file_path)

    if use_emulation:
        pulumi.log.info("KVM Emulation enabled for KubeVirt.")

    kubevirt_custom_resource_spec = {
        "configuration": {
            "developerConfiguration": {
                "useEmulation": use_emulation,
                "featureGates": [
                    "HostDevices",
                    "ExpandDisks",
                    "AutoResourceLimitsGate",
                ],
            },
            "smbios": {
                "sku": "kargo-kc2",
                "version": version,
                "manufacturer": "ContainerCraft",
                "product": "Kargo",
                "family": "CCIO",
            },
        }
    }

    kubevirt = CustomResource(
        "kubevirt",
        api_version="kubevirt.io/v1",
        kind="KubeVirt",
        metadata=ObjectMetaArgs(
            name="kubevirt",
            labels=labels,
            namespace=namespace,
            annotations=annotations,
        ),
        spec=kubevirt_custom_resource_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[operator],
        ),
    )

    return version, kubevirt

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

def get_latest_kubevirt_version() -> str:
    url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch latest KubeVirt version from {url}")
    return response.text.strip().lstrip("v")

def download_kubevirt_operator_yaml(version: str) -> Any:
    url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download KubeVirt operator YAML from {url}")
    return yaml.safe_load_all(response.text)

def _transform_yaml(yaml_data: Any, namespace: str) -> List[Dict[str, Any]]:
    transformed = []
    for resource in yaml_data:
        if resource.get('kind') == 'Namespace':
            continue
        if 'metadata' in resource:
            resource['metadata']['namespace'] = namespace
        transformed.append(resource)
    return transformed
