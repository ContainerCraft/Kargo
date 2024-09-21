# ./pulumi/core/init.py
# Description: Initializes Pulumi configuration, Kubernetes provider, and global resources.
import os
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider
from typing import Dict, Any, List

from .versions import load_default_versions
from .metadata import (
    collect_git_info,
    generate_git_labels,
    generate_git_annotations,
    set_global_labels,
    set_global_annotations
)
from .compliance import generate_compliance_labels, generate_compliance_annotations
from .types import ComplianceConfig
from .utils import generate_global_transformations

def initialize_pulumi() -> Dict[str, Any]:
    config = pulumi.Config()
    stack_name = pulumi.get_stack()
    project_name = pulumi.get_project()

    try:
        default_versions = load_default_versions(config)
        versions: Dict[str, str] = {}
        configurations: Dict[str, Dict[str, Any]] = {}
        global_depends_on: List[pulumi.Resource] = []

        kubernetes_config = config.get_object("kubernetes") or {}
        kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv('KUBECONFIG')
        kubernetes_context = kubernetes_config.get("context")

        pulumi.log.info(f"Kubeconfig: {kubeconfig}")
        pulumi.log.info(f"Kubernetes context: {kubernetes_context}")

        k8s_provider = Provider(
            "k8sProvider",
            kubeconfig=kubeconfig,
            context=kubernetes_context,
        )

        git_info = collect_git_info()
        configurations["source_repository"] = {
            "remote": git_info["remote"],
            "branch": git_info["branch"],
            "commit": git_info["commit"]
        }

        compliance_config_dict = config.get_object('compliance') or {}
        compliance_config = ComplianceConfig.merge(compliance_config_dict)
        compliance_labels = generate_compliance_labels(compliance_config)
        compliance_annotations = generate_compliance_annotations(compliance_config)

        git_labels = generate_git_labels(git_info)
        git_annotations = generate_git_annotations(git_info)
        global_labels = {**compliance_labels, **git_labels}
        global_annotations = {**compliance_annotations, **git_annotations}

        set_global_labels(global_labels)
        set_global_annotations(global_annotations)
        generate_global_transformations(global_labels, global_annotations)

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
    except Exception as e:
        pulumi.log.error(f"Initialization error: {str(e)}")
        raise
