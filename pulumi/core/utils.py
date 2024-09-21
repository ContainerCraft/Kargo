# ./pulumi/core/utils.py
# Description: Utility functions for sanitizing compliance metadata labels.

import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any

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

def sanitize_label_value(value: str) -> str:
    """
    Sanitizes a label value to comply with Kubernetes naming conventions.

    Args:
        value (str): The value to sanitize.

    Returns:
        str: The sanitized value.
    """
    value = value.lower()
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    return sanitized[:63]

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
