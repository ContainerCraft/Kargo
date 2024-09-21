# pulumi/core/utils.py

"""
Utility Functions Module

This module provides generic, reusable utility functions.
It includes resource transformations, Helm interactions, and miscellaneous helpers.
"""

import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any
import requests
import logging
import yaml
from packaging.version import parse as parse_version, InvalidVersion, Version

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    """
    Updates resource metadata with global labels and annotations.

    Args:
        metadata (Any): Metadata to update.
        global_labels (Dict[str, str]): Global labels to apply.
        global_annotations (Dict[str, str]): Global annotations to apply.
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

    Args:
        global_labels (Dict[str, str]): Global labels to apply.
        global_annotations (Dict[str, str]): Global annotations to apply.
    """
    def global_transform(args: pulumi.ResourceTransformationArgs) -> Optional[pulumi.ResourceTransformationResult]:
        props = args.props
        props.setdefault('metadata', {})
        set_resource_metadata(props['metadata'], global_labels, global_annotations)
        return pulumi.ResourceTransformationResult(props, args.opts)

    pulumi.runtime.register_stack_transformation(global_transform)

def get_latest_helm_chart_version(url: str, chart_name: str) -> str:
    """
    Fetches the latest stable version of a Helm chart from the given URL.

    Args:
        url (str): The URL of the Helm repository index.
        chart_name (str): The name of the Helm chart.

    Returns:
        str: The latest stable version of the chart.
    """
    try:
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        index = yaml.safe_load(response.content)
        if chart_name in index['entries']:
            chart_versions = index['entries'][chart_name]
            stable_versions = [v for v in chart_versions if is_stable_version(v['version'])]
            if not stable_versions:
                logging.info(f"No stable versions found for chart '{chart_name}'.")
                return "Chart not found"
            latest_chart = max(stable_versions, key=lambda x: parse_version(x['version']))
            return latest_chart['version']
        else:
            logging.info(f"No chart named '{chart_name}' found in repository.")
            return "Chart not found"

    except requests.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return f"Error fetching data: {e}"

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
