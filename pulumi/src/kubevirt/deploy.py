# src/kubevirt/deploy.py

import requests
import yaml
import tempfile
import os
from typing import Optional, List, Tuple, Dict

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions.CustomResource import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs

from src.lib.namespace import create_namespace
from src.lib.types import NamespaceConfig
from .types import KubeVirtConfig

def deploy_kubevirt_module(
        config_kubevirt: KubeVirtConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
        cert_manager_release: Optional[pulumi.Resource] = None
    ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
    """
    Deploys the KubeVirt module using YAML and custom resources.

    Args:
        config_kubevirt (KubeVirtConfig): Configuration object for KubeVirt deployment.
        global_depends_on (List[pulumi.Resource]): A list of resources that the deployment depends on.
        k8s_provider (k8s.Provider): The Kubernetes provider for this deployment.
        cert_manager_release (Optional[pulumi.Resource]): The cert-manager resource, if deployed.

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
        depends_on=global_depends_on  # Ensure it waits for any global dependencies like cert-manager
    )

    # Now deploy KubeVirt, ensuring it depends on the namespace creation
    kubevirt_version, kubevirt_operator = deploy_kubevirt(
        config_kubevirt=config_kubevirt,
        depends_on=[namespace_resource] + global_depends_on,
        k8s_provider=k8s_provider
    )

    if kubevirt_operator:
        # Optionally add KubeVirt to global dependencies
        global_depends_on.append(kubevirt_operator)

    return kubevirt_version, kubevirt_operator


def deploy_kubevirt(
        config_kubevirt: KubeVirtConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider
    ) -> Tuple[str, k8s.yaml.ConfigFile]:
    """
    Deploys KubeVirt into the Kubernetes cluster using its YAML manifests.

    Args:
        config_kubevirt (KubeVirtConfig): Configuration settings for KubeVirt.
        depends_on (List[pulumi.Resource]): Resources that the deployment should depend on.
        k8s_provider (k8s.Provider): The Kubernetes provider instance.

    Returns:
        Tuple[str, k8s.yaml.ConfigFile]:
            - The version of KubeVirt deployed.
            - The KubeVirt operator resource.
    """
    # Extract configuration details from the KubeVirtConfig object
    namespace = config_kubevirt.namespace
    version = config_kubevirt.version
    use_emulation = config_kubevirt.use_emulation

    # Fetch or use the specified KubeVirt version
    if version == 'latest' or version is None:
        kubevirt_stable_version_url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
        version = requests.get(kubevirt_stable_version_url).text.strip().lstrip("v")
        pulumi.log.info(f"Setting KubeVirt release version to latest: {version}")
    else:
        pulumi.log.info(f"Using KubeVirt version: {version}")

    # Download the KubeVirt operator YAML
    kubevirt_operator_url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    response = requests.get(kubevirt_operator_url)
    kubevirt_yaml = yaml.safe_load_all(response.text)

    # Transform the YAML and set the correct namespace
    transformed_yaml = _transform_yaml(kubevirt_yaml, namespace)

    # Write the transformed YAML to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    # Deploy the KubeVirt operator
    operator = k8s.yaml.ConfigFile(
        'kubevirt-operator',
        file=temp_file_path,
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

    # Create the KubeVirt custom resource
    kubevirt = CustomResource(
        "kubevirt",
        api_version="kubevirt.io/v1",
        kind="KubeVirt",
        metadata=ObjectMetaArgs(
            name="kubevirt",
            namespace=namespace,
        ),
        spec=kubevirt_custom_resource_spec,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=None,
            depends_on=[operator],
        )
    )

    return version, operator


def _transform_yaml(yaml_data, namespace: str) -> List[Dict]:
    """
    Helper function to transform YAML to set namespace and modify resources.

    Args:
        yaml_data: The YAML data to transform.
        namespace: The namespace to set for the resources.

    Returns:
        List[Dict]: The transformed YAML with the appropriate namespace.
    """
    transformed = []
    for resource in yaml_data:
        if resource.get('kind') == 'Namespace':
            continue  # Skip the Namespace resource
        if 'metadata' in resource:
            resource['metadata']['namespace'] = namespace
        transformed.append(resource)
    return transformed
