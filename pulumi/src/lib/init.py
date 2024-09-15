# src/lib/init.py

import os
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider
from typing import Dict, List, Any

from src.lib.versions import load_default_versions
from src.lib.metadata import collect_git_info

def initialize_pulumi() -> Dict[str, Any]:
    """
    Initializes the Pulumi configuration, Kubernetes provider, and global resources.

    Returns:
        A dictionary containing initialized resources like:
        - config: Pulumi Config object
        - stack_name: The Pulumi stack name
        - project_name: The Pulumi project name
        - versions: Dictionary to track deployed component versions
        - configurations: Dictionary to track module configurations
        - global_depends_on: List to manage dependencies globally
        - k8s_provider: Kubernetes provider instance
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
    # TODO: populate global resource tags / labels / annotations with Git metadata
    configurations["source_repository"] = {
        "remote": git_info["remote"],
        "branch": git_info["branch"],
        "commit": git_info["commit"]
    }

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
        "git_info": git_info
    }
