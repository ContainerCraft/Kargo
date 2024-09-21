# ./pulumi/core/utils.py
# Description: Utility functions for sanitizing compliance metadata labels.

import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any


def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    if isinstance(metadata, dict):
        if metadata.get('labels') is None:
            metadata['labels'] = {}
        metadata.setdefault('labels', {}).update(global_labels)

        if metadata.get('annotations') is None:
            metadata['annotations'] = {}
        metadata.setdefault('annotations', {}).update(global_annotations)

    elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
        if metadata.labels is None:
            metadata.labels = {}
        metadata.labels.update(global_labels)

        if metadata.annotations is None:
            metadata.annotations = {}
        metadata.annotations.update(global_annotations)


def generate_global_transformations(global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    def global_transform(args: pulumi.ResourceTransformationArgs) -> Optional[pulumi.ResourceTransformationResult]:
        props = args.props
        if 'metadata' in props:
            metadata = props['metadata']
            set_resource_metadata(metadata, global_labels, global_annotations)
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
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    return sanitized[:63]

def extract_repo_name(remote_url: str) -> str:
    match = re.search(r'[:/]([^/:]+/[^/\.]+)(\.git)?$', remote_url)
    if match:
        return match.group(1)
    return remote_url
