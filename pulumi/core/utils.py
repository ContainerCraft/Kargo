# pulumi/core/utils.py

"""
Utility Functions Module

This module provides generic, reusable utility functions.
It includes resource transformations, Helm interactions, and miscellaneous helpers.
"""

import re
import os
import tempfile
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any, List
import requests
import logging
import yaml
from packaging.version import parse as parse_version, InvalidVersion, Version


# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    """
    Updates resource metadata with global labels and annotations.
    """
    if isinstance(metadata, dict):
        metadata.setdefault('labels', {}).update(global_labels)
        metadata.setdefault('annotations', {}).update(global_annotations)
    elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
        if metadata.labels is None:
            metadata.labels = {}
        metadata.labels.update(global_labels)
        if metadata.annotations is None:
            metadata.annotations = {}
        metadata.annotations.update(global_annotations)

def generate_global_transformations(global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    """
    Generates global transformations for resources.
    """
    def global_transform(args: pulumi.ResourceTransformationArgs) -> Optional[pulumi.ResourceTransformationResult]:
        props = args.props

        if 'metadata' in props:
            set_resource_metadata(props['metadata'], global_labels, global_annotations)
        elif 'spec' in props and isinstance(props['spec'], dict):
            if 'metadata' in props['spec']:
                set_resource_metadata(props['spec']['metadata'], global_labels, global_annotations)

        return pulumi.ResourceTransformationResult(props, args.opts)

    pulumi.runtime.register_stack_transformation(global_transform)

def get_latest_helm_chart_version(repo_url: str, chart_name: str) -> str:
    """
    Fetches the latest stable version of a Helm chart from the given repository URL.

    Args:
        repo_url (str): The base URL of the Helm repository.
        chart_name (str): The name of the Helm chart.

    Returns:
        str: The latest stable version of the chart.
    """
    try:
        index_url = repo_url.rstrip('/') + '/index.yaml'

        logging.info(f"Fetching Helm repository index from URL: {index_url}")
        response = requests.get(index_url)
        response.raise_for_status()

        index = yaml.safe_load(response.content)
        if chart_name in index['entries']:
            chart_versions = index['entries'][chart_name]
            stable_versions = [v for v in chart_versions if is_stable_version(v['version'])]
            if not stable_versions:
                logging.info(f"No stable versions found for chart '{chart_name}'.")
                return "Chart not found"
            latest_chart = max(stable_versions, key=lambda x: parse_version(x['version']))
            return latest_chart['version'].lstrip('v')
        else:
            logging.info(f"No chart named '{chart_name}' found in repository.")
            return "Chart not found"

    except requests.RequestException as e:
        logging.error(f"Error fetching Helm repository index: {e}")
        return f"Error fetching data: {e}"
    except yaml.YAMLError as e:
        logging.error(f"Error parsing Helm repository index YAML: {e}")
        return f"Error parsing YAML: {e}"

def is_stable_version(version_str: str) -> bool:
    """
    Determines if a version string represents a stable version.

    Args:
        version_str (str): The version string to check.

    Returns:
        bool: True if the version is stable, False otherwise.
    """
    try:
        parsed_version = parse_version(version_str)
        return isinstance(parsed_version, Version) and not parsed_version.is_prerelease and not parsed_version.is_devrelease
    except InvalidVersion:
        return False

def extract_repo_name(remote_url: str) -> str:
    """
    Extracts the repository name from a Git remote URL.

    Args:
        remote_url (str): The Git remote URL.

    Returns:
        str: The repository name.
    """
    match = re.search(r'[:/]([^/:]+/[^/\.]+)(\.git)?$', remote_url)
    if match:
        return match.group(1)
    return remote_url


# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_crds(crd_names: List[str], k8s_provider: k8s.Provider, depends_on: List[pulumi.Resource], parent: pulumi.Resource) -> List[pulumi.Resource]:
    """
    Waits for the specified CRDs to be present and ensures dependencies.

    Args:
        crd_names (List[str]): A list of CRD names.
        k8s_provider (k8s.Provider): The Kubernetes provider.
        depends_on (List[pulumi.Resource]): A list of dependencies.
        parent (pulumi.Resource): The parent resource.

    Returns:
        List[pulumi.Resource]: The CRD resources or an empty list during preview.
    """
    crds = []

    for crd_name in crd_names:
        try:
            crd = k8s.apiextensions.v1.CustomResourceDefinition.get(
                resource_name=crd_name,
                id=crd_name,
                opts=pulumi.ResourceOptions(
                    provider=k8s_provider,
                    depends_on=depends_on,
                    parent=parent,
                ),
            )
            crds.append(crd)
        except Exception:
            pulumi.log.info(f"CRD {crd_name} not found, creating dummy CRD.")
            dummy_crd = create_dummy_crd(crd_name, k8s_provider, depends_on, parent)
            if dummy_crd:
                crds.append(dummy_crd)

    return crds

def create_dummy_crd(crd_name: str, k8s_provider: k8s.Provider, depends_on: List[pulumi.Resource], parent: pulumi.Resource) -> Optional[k8s.yaml.ConfigFile]:
    """
    Create a dummy CRD definition to use during preview runs.

    Args:
        crd_name (str): The name of the CRD.
        k8s_provider (k8s.Provider): The Kubernetes provider.
        depends_on (List[pulumi.Resource]): A list of dependencies.
        parent (pulumi.Resource): The parent resource.

    Returns:
        Optional[k8s.yaml.ConfigFile]: The dummy CRD resource.
    """
    parts = crd_name.split('.')
    plural = parts[0]
    group = '.'.join(parts[1:])
    kind = ''.join(word.title() for word in plural.split('_'))

    dummy_crd_yaml_template = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: {metadata_name}
spec:
  group: {group}
  names:
    plural: {plural}
    kind: {kind}
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
"""

    dummy_crd_yaml = dummy_crd_yaml_template.format(
        metadata_name=f"{plural}.{group}",
        group=group,
        plural=plural,
        kind=kind,
    )

    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write(dummy_crd_yaml)
            temp_file_path = temp_file.name

        dummy_crd = k8s.yaml.ConfigFile(
            "dummy-crd-{}".format(crd_name),
            file=temp_file_path,
            opts=pulumi.ResourceOptions(
                parent=parent,
                depends_on=depends_on,
                provider=k8s_provider,
            )
        )
        return dummy_crd
    finally:
        os.unlink(temp_file_path)
