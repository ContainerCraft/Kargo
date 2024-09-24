# pulumi/modules/kubevirt/deploy.py

"""
Deploys the KubeVirt module.

This module is responsible for deploying KubeVirt on the Kubernetes cluster.

The configuration options are:

    namespace: str - The namespace where KubeVirt will be deployed. Default is 'kubevirt'.
    version: Optional[str] - The version of KubeVirt to deploy. Default is None.
    use_emulation: bool - Whether to use emulation or not. Default is False.
    labels: Dict[str, str] - The labels to apply to the KubeVirt resources. Default is {}.
    annotations: Dict[str, Any] - The annotations to apply to the KubeVirt resources. Default is {}.
    global_depends_on: List[pulumi.Resource] - The list of resources that the KubeVirt module depends on. Default is [].
    k8s_provider: k8s.Provider - The Kubernetes provider. Default is None.

    Returns:
        Tuple[Optional[str], k8s.apiextensions.CustomResource] - The version of KubeVirt deployed and the deployed resource.

    Raises:
        Exception: If the KubeVirt CRDs are not available.
"""

# Import necessary modules
import requests
import yaml
import tempfile
import os
from typing import Optional, List, Tuple, Dict, Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi import log

from core.utils import wait_for_crds
from core.metadata import get_global_labels, get_global_annotations
from core.resource_helpers import (
    create_namespace,
    create_custom_resource,
    create_config_file,
)
from .types import KubeVirtConfig

def deploy_kubevirt_module(
        config_kubevirt: KubeVirtConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[Optional[str], k8s.apiextensions.CustomResource]:
    """
    Deploys the KubeVirt module and returns the version and the deployed resource.
    """
    # Deploy KubeVirt
    kubevirt_version, kubevirt_resource = deploy_kubevirt(
        config_kubevirt=config_kubevirt,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Update global dependencies if not None
    # TODO: re-evaluate if global_depends_on should be updated here or in the calling function
    # TODO: regardless, the if statement is not necessary as this code will not be executed if kubevirt module is not enabled
    if kubevirt_resource:
        global_depends_on.append(kubevirt_resource)

    return kubevirt_version, kubevirt_resource

def deploy_kubevirt(
        config_kubevirt: KubeVirtConfig,
        depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[str, Optional[pulumi.Resource]]:
    """
    Deploys KubeVirt operator and creates the KubeVirt CustomResource,
    ensuring that the CRD is available before creating the CustomResource.
    """
    # Create Namespace using the helper function from core/resource_helpers.py
    namespace_resource = create_namespace(
        name=config_kubevirt.namespace,
        k8s_provider=k8s_provider,
        parent=k8s_provider,
        depends_on=depends_on,
    )

    # Add the namespace to the dependencies
    # TODO: reevaluate if this is necessary, helpful, and if a module scoped `module_depends_on` pattern should be adopted across modules
    depends_on = depends_on + [namespace_resource]

    # Extract config objects from config dictionary
    version = config_kubevirt.version
    namespace = config_kubevirt.namespace
    use_emulation = config_kubevirt.use_emulation

    # Determine latest version release from GitHub Releases
    # TODO: reimplement into the get_module_config function and adopt across all modules to reduce code duplication
    if version == 'latest' or version is None:
        version = get_latest_kubevirt_version()
        log.info(f"Setting KubeVirt release version to latest: {version}")
    else:
        log.info(f"Using KubeVirt version: {version}")

    # Download and transform KubeVirt operator YAML
    kubevirt_operator_yaml = download_kubevirt_operator_yaml(version)
    transformed_yaml = _transform_yaml(kubevirt_operator_yaml, namespace)

    # Write transformed YAML to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        yaml.dump_all(transformed_yaml, temp_file)
        temp_file_path = temp_file.name

    operator = None
    try:
        # Deploy KubeVirt operator using the helper function
        operator = create_config_file(
            name='kubevirt-operator',
            file=temp_file_path,
            opts=pulumi.ResourceOptions(
                parent=namespace_resource,
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="5m",
                    delete="5m",
                ),
            ),
            k8s_provider=k8s_provider,
            depends_on=depends_on,
        )
    finally:
        os.unlink(temp_file_path)

    # Wait for the CRDs to be registered
    crds = wait_for_crds(
        crd_names=[
            "kubevirts.kubevirt.io",
            # Add other required CRD names here if needed
        ],
        k8s_provider=k8s_provider,
        depends_on=depends_on,
        parent=operator
    )

    # Create the KubeVirt resource always
    kubevirt_resource = create_custom_resource(
        name="kubevirt",
        args={
            "apiVersion": "kubevirt.io/v1",
            "kind": "KubeVirt",
            "metadata": {
                "name": "kubevirt",
                "namespace": namespace,
            },
            "spec": {
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
                },
            },
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=operator,
            depends_on=depends_on + crds,
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="5m",
                delete="5m",
            ),
        ),
    )

    return version, kubevirt_resource


# Function to get the latest KubeVirt version if the version is set to 'latest' or no version configuration is supplied
def get_latest_kubevirt_version() -> str:
    """
    Retrieves the latest stable version of KubeVirt.
    """

    # TODO: relocate this URL to a default in the KubevirtConfig class and allow for an override
    url = 'https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch latest KubeVirt version from {url}")
    return response.text.strip().lstrip("v")

def download_kubevirt_operator_yaml(version: str) -> Any:
    """
    Downloads the KubeVirt operator YAML for the specified version.
    """

    # TODO: relocate this URL to a default in the KubevirtConfig class and allow for an override
    # TODO: support remote or local kubevirt-operator.yaml file
    url = f'https://github.com/kubevirt/kubevirt/releases/download/v{version}/kubevirt-operator.yaml'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download KubeVirt operator YAML from {url}")
    return list(yaml.safe_load_all(response.text))

# Function to remove Namespace resources from the YAML data and replace other object namespaces with the specified namespace value as an override
def _transform_yaml(yaml_data: Any, namespace: str) -> List[Dict[str, Any]]:
    """
    Transforms the YAML data to set the namespace and exclude Namespace resources.
    """
    transformed = []
    for resource in yaml_data:
        if resource.get('kind') == 'Namespace':
            continue
        if 'metadata' in resource:
            resource['metadata']['namespace'] = namespace
        transformed.append(resource)
    return transformed
