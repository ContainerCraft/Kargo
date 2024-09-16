# src/lib/init.py
# Description: Initializes Pulumi configuration, Kubernetes provider, and global resources.

import os
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider
from typing import Dict, List, Any

from src.lib.versions import load_default_versions
from src.lib.metadata import (
    collect_git_info,
    generate_git_labels,
    generate_git_annotations,
    set_global_labels,
    set_global_annotations
)
from src.lib.compliance import generate_compliance_labels, generate_compliance_annotations
from src.lib.types import ComplianceConfig
from src.lib.utils import generate_global_transformations

def initialize_pulumi() -> Dict[str, Any]:
    """
    Initializes the Pulumi configuration, Kubernetes provider, and global resources.
    """
    # Load Pulumi config
    config = pulumi.Config()
    stack_name = pulumi.get_stack()
    project_name = pulumi.get_project()

    # Load default versions for modules
    default_versions = load_default_versions(config)

    # Initialize dictionaries for versions and configurations
    versions: Dict[str, str] = {}
    configurations: Dict[str, Dict[str, Any]] = {}

    # Initialize a list to manage dependencies globally
    global_depends_on: List[pulumi.Resource] = []

    # Retrieve Kubernetes settings from Pulumi config or environment variables
    kubernetes_config = config.get_object("kubernetes") or {}
    kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv('KUBECONFIG')
    kubernetes_context = kubernetes_config.get("context")

    # Log the Kubernetes configuration details
    pulumi.log.info(f"kubeconfig: {kubeconfig}")
    pulumi.log.info(f"kubernetes_context: {kubernetes_context}")

    # Create a Kubernetes provider instance
    k8s_provider = Provider(
        "k8sProvider",
        kubeconfig=kubeconfig,
        context=kubernetes_context,
    )

    # Retrieve the Git repository source, branch, and commit metadata
    git_info = collect_git_info()

    # Append Git metadata to the configurations dictionary under 'source_repository'
    configurations["source_repository"] = {
        "remote": git_info["remote"],
        "branch": git_info["branch"],
        "commit": git_info["commit"]
    }

    # Collect compliance configuration
    compliance_config_dict = config.get_object('compliance') or {}
    compliance_config = ComplianceConfig.merge(compliance_config_dict)

    # Generate compliance labels and annotations
    compliance_labels = generate_compliance_labels(compliance_config)
    compliance_annotations = generate_compliance_annotations(compliance_config)

    # Generate Git labels and annotations
    git_labels = generate_git_labels(git_info)
    git_annotations = generate_git_annotations(git_info)

    # Combine labels and annotations
    global_labels = {**compliance_labels, **git_labels}
    global_annotations = {**compliance_annotations, **git_annotations}

    # Store global labels and annotations for access in other modules
    set_global_labels(global_labels)
    set_global_annotations(global_annotations)

    # Apply global transformations to all resources
    generate_global_transformations(global_labels, global_annotations)

    # Return all initialized resources
    return {
        "config": config,
        "stack_name": stack_name,
        "project_name": project_name,
        "default_versions": default_versions,
        "versions": versions,
        "configurations": configurations,
        "global_depends_on": global_depends_on,
        "k8s_provider": k8s_provider,
        "git_info": git_info,
        "compliance_config": compliance_config,
        "global_labels": global_labels,
        "global_annotations": global_annotations,
    }
