# core/utils.py
# Description: Utility functions for sanitizing compliance metadata labels.

import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional

def generate_global_transformations(global_labels: dict, global_annotations: dict):
    """
    Registers a global transformation function that applies the provided labels and annotations to all resources.
    """
    def global_transform(args: pulumi.ResourceTransformationArgs) -> Optional[pulumi.ResourceTransformationResult]:
        props = args.props
        if 'metadata' in props:
            metadata = props['metadata']
            if isinstance(metadata, dict):
                metadata.setdefault('labels', {})
                metadata['labels'].update(global_labels)
                metadata.setdefault('annotations', {})
                metadata['annotations'].update(global_annotations)
            elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
                if metadata.labels is None:
                    metadata.labels = {}
                metadata.labels = {**metadata.labels, **global_labels}
                if metadata.annotations is None:
                    metadata.annotations = {}
                metadata.annotations = {**metadata.annotations, **global_annotations}
                props['metadata'] = metadata
        else:
            props['metadata'] = {
                'labels': global_labels,
                'annotations': global_annotations
            }
        return pulumi.ResourceTransformationResult(props, args.opts)

    pulumi.runtime.register_stack_transformation(global_transform)

def sanitize_label_value(value: str) -> str:
    value = value.lower()
    # Replace invalid characters with '-'
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    # Remove leading and trailing non-alphanumeric characters
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    # Truncate to 63 characters
    return sanitized[:63]

def extract_repo_name(remote_url: str) -> str:
    # Extract the repository name from the remote URL
    # Example: 'https://github.com/ContainerCraft/Kargo.git' -> 'ContainerCraft/Kargo'
    match = re.search(r'[:/]([^/:]+/[^/\.]+)(\.git)?$', remote_url)
    if match:
        return match.group(1)
    return remote_url
