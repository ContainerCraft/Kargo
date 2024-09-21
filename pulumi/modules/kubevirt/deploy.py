# ./pulumi/modules/kubevirt/deploy.py
# Description:

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
from core.namespace import create_namespace
from core.metadata import get_global_labels, get_global_annotations

from .types import KubeVirtConfig

def deploy_kubevirt_module(
        config_kubevirt: KubeVirtConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
    """
    Deploys the KubeVirt module with labels and annotations.

    Args:
        config_kubevirt (KubeVirtConfig): Configuration object for KubeVirt deployment.
        global_depends_on (List[pulumi.Resource]): A list of resources that the deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.

    Returns:
        Tuple[Optional[str], Optional[pulumi.Resource]]:
            - The deployed KubeVirt version.
            - The KubeVirt operator resource.
    """
    # Create the namespace for KubeVirt first, independently
    namespace_config = NamespaceConfig(name=config_kubevirt.namespace)
    namespace_resource = create_namespace(
        config=namespace_config,
        k8s_provider=k8s_provider,
        depends_on=global_depends_on
    )

    # Now deploy KubeVirt, ensuring it depends on the namespace creation
    kubevirt_version, kubevirt_operator = deploy_kubevirt(
        config_kubevirt=config_kubevirt,
        depends_on=[namespace_resource],
        k8s_provider=k8s_provider,
        namespace_resource=namespace_resource
    )

    # Optionally add KubeVirt to global dependencies
    global_depends_on.append(kubevirt_operator)

    return kubevirt_version, kubevirt_operator


def deploy_kubevirt(
        config_kubevirt: KubeVirtConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
        namespace_resource: pulumi.Resource
    ) -> Tuple[str, k8s.yaml.ConfigFile]:
    """
    Deploys KubeVirt into the Kubernetes cluster using its YAML manifests and applies labels and annotations.

    Args:
        config_kubevirt (KubeVirtConfig): Configuration object for KubeVirt deployment.
        depends_on (List[pulumi.Resource]): List of resources that this deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.
        namespace_resource (pulumi.Resource): The namespace resource.

    Returns:
        Tuple[str, k8s.yaml.ConfigFile]: The KubeVirt version and the operator resource.
    """
    # Extract configuration details from the KubeVirtConfig object
    namespace = config_kubevirt.namespace
    version = config_kubevirt.version
    use_emulation = config_kubevirt.use_emulation
    labels = config_kubevirt.labels
    annotations = config_kubevirt.annotations

    # Fetch or use the specified KubeVirt version
    if version == 'latest' or version is None:
        kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
        response = requests.get(kubevirt_stable_version_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch latest KubeVirt version from {kubevirt_stable_version_url}")
        version = response.text.strip().lstrip("v")
        pulumi.log.info(f"Setting KubeVirt release version to latest: {version}")
    else:
        pulumi.log.info(f"Using KubeVirt version: {version}")

    # Download the KubeVirt operator YAML
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    response = requests.get(kubevirt_operator_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download KubeVirt operator YAML from {kubevirt_operator_url}")
    kubevirt_yaml = yaml.safe_load_all(response.text)

    # Transform the YAML and set the correct namespace
    transformed_yaml = _transform_yaml(kubevirt_yaml, namespace)

    def kubevirt_transform(obj: Dict[str, Any], opts: pulumi.ResourceOptions) -> pulumi.ResourceTransformationResult:
        """
        Transformation function to add labels and annotations to Kubernetes objects
        in the KubeVirt operator YAML manifests.

        Args:
            obj (Dict[str, Any]): The resource object to transform.
            opts (pulumi.ResourceOptions): The resource options for the transformation.

        Returns:
            pulumi.ResourceTransformationResult: The transformed resource and options.
        """
        # Ensure the 'metadata' field exists in the object
        obj.setdefault("metadata", {})

        # Apply labels
        obj["metadata"].setdefault("labels", {})
        obj["metadata"]["labels"].update(labels)

        # Apply annotations
        obj["metadata"].setdefault("annotations", {})
        obj["metadata"]["annotations"].update(annotations)

        # If this is a Pod or a Deployment, ensure the template also has metadata
        if "spec" in obj and "template" in obj["spec"]:
            obj["spec"]["template"].setdefault("metadata", {})
            obj["spec"]["template"]["metadata"].setdefault("labels", {})
            obj["spec"]["template"]["metadata"]["labels"].update(labels)
            obj["spec"]["template"]["metadata"].setdefault("annotations", {})
            obj["spec"]["template"]["metadata"]["annotations"].update(annotations)

        return pulumi.ResourceTransformationResult(obj, opts)

    # Write the transformed YAML to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    try:
        # Deploy the KubeVirt operator with transformation
        operator = k8s.yaml.ConfigFile(
            'kubevirt-operator',
            file=temp_file_path,
            transformations=[kubevirt_transform],
            opts=pulumi.ResourceOptions(
                provider=k8s_provider,
                parent=None,
                depends_on=depends_on,
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="5m",
                    delete="5m"
                )
            )
        )
    finally:
        # Clean up the temporary file after Pulumi has used it
        pulumi.Output.all().apply(lambda _: os.unlink(temp_file_path))

    # Deploy the KubeVirt custom resource
    if use_emulation:
        pulumi.log.info("KVM Emulation enabled for KubeVirt.")

    # Create the KubeVirt custom resource object
    kubevirt_custom_resource_spec = {
        "configuration": {
            "developerConfiguration": {
                "useEmulation": use_emulation,
                "featureGates": [
                    "HostDevices",
                    "ExpandDisks",
                    "AutoResourceLimitsGate"
                ]
            },
            "smbios": {
                "sku": "kargo-kc2",
                "version": version,
                "manufacturer": "ContainerCraft",
                "product": "Kargo",
                "family": "CCIO"
            }
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
            annotations=annotations
        ),
        spec=kubevirt_custom_resource_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace_resource,
            depends_on=[operator],
        )
    )

    return version, operator


def _transform_yaml(yaml_data: Any, namespace: str) -> List[Dict[str, Any]]:
    """
    Helper function to transform YAML to set namespace and modify resources.

    Args:
        yaml_data: The YAML data to transform.
        namespace: The namespace to set for the resources.

    Returns:
        List[Dict[str, Any]]: The transformed YAML with the appropriate namespace.
    """
    transformed = []
    for resource in yaml_data:
        if resource.get('kind') == 'Namespace':
            continue
        if 'metadata' in resource:
            resource['metadata']['namespace'] = namespace
        transformed.append(resource)
    return transformed
