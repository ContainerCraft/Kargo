# ./pulumi/core/utils.py
# Description: Utility functions for sanitizing compliance metadata labels.

import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict


def generate_global_transformations(global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    """
    Registers a global transformation function that applies the provided labels and annotations to all resources.

    Args:
        global_labels (Dict[str, str]): Global label set to apply to all resources.
        global_annotations (Dict[str, str]): Global annotations to apply to all resources.
    """
    def global_transform(args: pulumi.ResourceTransformationArgs) -> Optional[pulumi.ResourceTransformationResult]:
        props = args.props
        if 'metadata' in props:
            metadata = props['metadata']
            if isinstance(metadata, dict):
                if metadata.get('labels') is None:
                    metadata['labels'] = {}
                metadata['labels'].update(global_labels)

                if metadata.get('annotations') is None:
                    metadata['annotations'] = {}
                metadata['annotations'].update(global_annotations)

            elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
                if metadata.labels is None:
                    metadata.labels = {}
                metadata.labels.update(global_labels)

                if metadata.annotations is None:
                    metadata.annotations = {}
                metadata.annotations.update(global_annotations)
                props['metadata'] = metadata
        else:
            props['metadata'] = {
                'labels': global_labels,
                'annotations': global_annotations
            }
        return pulumi.ResourceTransformationResult(props, args.opts)

    pulumi.runtime.register_stack_transformation(global_transform)

def sanitize_label_value(value: str) -> str:
    """
    Sanitize label values to meet Kubernetes metadata requirements.

    Replaces invalid characters with '-'

    Args:
        value (str): The string value to sanitize.

    Returns:
        str: The sanitized string value, truncated to 63 characters.
    """
    value = value.lower()
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)  # Remove leading non-alphanumeric chars
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)  # Remove trailing non-alphanumeric chars
    return sanitized[:63]

def extract_repo_name(remote_url: str) -> str:
    """
    Extract the repository name from the remote URL.

    Example: 'https://github.com/ContainerCraft/Kargo.git' -> 'ContainerCraft/Kargo'

    Args:
        remote_url (str): The remote URL from which to extract the repo name.

    Returns:
        str: The extracted repository name.
    """
    match = re.search(r'[:/]([^/:]+/[^/\.]+)(\.git)?$', remote_url)
    if match:
        return match.group(1)
    return remote_url
