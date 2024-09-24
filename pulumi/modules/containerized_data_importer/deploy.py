# pulumi/modules/containerized_data_importer/deploy.py

"""
Enhanced deployment script for the Containerized Data Importer (CDI) module.
"""

import requests
from typing import List, Dict, Any, Tuple, Optional

import pulumi
import pulumi_kubernetes as k8s
from pulumi import log

from core.resource_helpers import create_namespace, create_custom_resource

from .types import CdiConfig

def deploy_containerized_data_importer_module(
        config_cdi: CdiConfig,
        global_depends_on: List[pulumi.Resource],
        k8s_provider: k8s.Provider,
    ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
    """
    Deploys the Containerized Data Importer (CDI) module and returns the version and the deployed resource.

    Args:
        config_cdi (CdiConfig): Configuration for the CDI module.
        global_depends_on (List[pulumi.Resource]): Global dependencies for all modules.
        k8s_provider (k8s.Provider): The Kubernetes provider.

    Returns:
        Tuple[Optional[str], Optional[pulumi.Resource]]: The version deployed and the deployed resource.
    """
    try:
        log.info("Starting deployment of CDI module")

        version = config_cdi.version if config_cdi.version and config_cdi.version != "latest" else fetch_latest_version()
        log.info(f"Using CDI version: {version}")

        # Create namespace
        log.info(f"Creating namespace: {config_cdi.namespace}")
        namespace_resource = create_namespace(
            name=config_cdi.namespace,
            labels=config_cdi.labels,
            annotations=config_cdi.annotations,
            k8s_provider=k8s_provider,
            parent=k8s_provider,
            depends_on=global_depends_on,
        )

        # Deploy CDI operator
        # TODO: consider moving url variable to config via new value in ContainerizedDataImporterConfig class with default value, may require helper function in <module>/types.py to support `latest`
        operator_url = f"https://github.com/kubevirt/containerized-data-importer/releases/download/v{version}/cdi-operator.yaml"
        log.info(f"Deploying CDI operator from URL: {operator_url}")

        operator_resource = k8s.yaml.ConfigFile(
            "cdi-operator",
            file=operator_url,
            opts=pulumi.ResourceOptions(
                provider=k8s_provider,
                parent=namespace_resource,
            )
        )

        # Ensure dependencies on operator and namespace
        # TODO: re-evaluate implementing module specific module_depends_on and consistently adopting across all modules
        depends_on = global_depends_on + [operator_resource]

        # Create CDI custom resource
        log.info("Creating CDI custom resource")
        cdi_resource = create_custom_resource(
            name="cdi",
            args={
                "apiVersion": "cdi.kubevirt.io/v1beta1",
                "kind": "CDI",
                "metadata": {
                    "name": "cdi",
                    "namespace": config_cdi.namespace,
                },
                "spec": {
                    "config": {
                        "featureGates": [
                            "HonorWaitForFirstConsumer",
                        ],
                    },
                    "imagePullPolicy": "IfNotPresent",
                    "infra": {
                        "nodeSelector": {
                            "kubernetes.io/os": "linux",
                        },
                        "tolerations": [
                            {
                                "key": "CriticalAddonsOnly",
                                "operator": "Exists",
                            },
                        ],
                    },
                    "workload": {
                        "nodeSelector": {
                            "kubernetes.io/os": "linux",
                        },
                    },
                },
            },
            opts=pulumi.ResourceOptions(
                parent=operator_resource,
                depends_on=namespace_resource,
                provider=k8s_provider,
                custom_timeouts=pulumi.CustomTimeouts(create="1m", update="1m", delete="1m"),
            )
        )

        log.info("CDI module deployment complete")
        return version, operator_resource

    except Exception as e:
        log.error(f"Deployment of CDI module failed: {str(e)}")
        raise

# Function to fetch the latest stable semantic version from GitHub releases
# TODO: consider making github latest release version fetching a shared utility function & adopting across all modules to reduce code duplication
def fetch_latest_version() -> str:
    """
    Fetches the latest stable version of CDI from GitHub releases.

    Returns:
        str: Latest stable version string.
    """
    try:
        latest_release_url = 'https://github.com/kubevirt/containerized-data-importer/releases/latest'
        tag = requests.get(latest_release_url, allow_redirects=False).headers.get('location')
        version = tag.split('/')[-1]
        version = version.lstrip('v')
        log.info(f"Fetched latest CDI version: {version}")
        return version
    except Exception as e:
        log.error(f"Error fetching the latest version: {e}")
        return "latest"
