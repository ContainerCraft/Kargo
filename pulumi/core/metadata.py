# pulumi/core/metadata.py
# TODO:
# - enhance with support for propagation of labels annotations on AWS resources
# - enhance by adding additional data to global tag / label / annotation metadata
# - support adding git release semver to global tag / label / annotation metadata

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It includes functions to generate compliance and Git-related metadata.
"""

import re
import json
import threading
import subprocess
from typing import Dict, Any

import pulumi
from pulumi import log

from .types import ComplianceConfig

# Singleton class to manage global metadata
# Globals are correctly chosen to enforce consistency across all modules and resources
# This class is thread-safe and used to store global labels and annotations
class MetadataSingleton:
    _instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls.__lock:
                if not cls._instance:
                    cls._instance = super(MetadataSingleton, cls).__new__(cls)
                    cls._instance._data = {"_global_labels": {}, "_global_annotations": {}}
        return cls._instance

def set_global_labels(labels: Dict[str, str]):
    """
    Sets global labels.

    Args:
        labels (Dict[str, str]): The global labels.
    """
    MetadataSingleton()._data["_global_labels"] = labels

def set_global_annotations(annotations: Dict[str, str]):
    """
    Sets global annotations.

    Args:
        annotations (Dict[str, str]): The global annotations.
    """
    MetadataSingleton()._data["_global_annotations"] = annotations

def get_global_labels() -> Dict[str, str]:
    """
    Retrieves global labels.

    Returns:
        Dict[str, str]: The global labels.
    """
    return MetadataSingleton()._data["_global_labels"]

def get_global_annotations() -> Dict[str, str]:
    """
    Retrieves global annotations.

    Returns:
        Dict[str, str]: The global annotations.
    """
    return MetadataSingleton()._data["_global_annotations"]

# Function to collect Git repository information
# TODO: re-implement this function to use the GitPython library or other more pythonic approach
# TODO: add support for fetching and returning the latest git release semver
def collect_git_info() -> Dict[str, str]:
    """
    Collects Git repository information.

    Returns:
        Dict[str, str]: The Git information.
    """
    try:
        remote = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        return {'remote': remote, 'branch': branch, 'commit': commit}
    except subprocess.CalledProcessError as e:
        log.error(f"Error fetching git information: {e}")
        return {'remote': 'N/A', 'branch': 'N/A', 'commit': 'N/A'}

def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related labels.

    Args:
        git_info (Dict[str, str]): The Git information.

    Returns:
        Dict[str, str]: The git-related labels.
    """
    return {
        "git.branch": git_info.get("branch", ""),
        "git.commit": git_info.get("commit", "")[:7],
    }

def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related annotations.

    Args:
        git_info (Dict[str, str]): The Git information.

    Returns:
        Dict[str, str]: The git-related annotations.
    """
    return {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", "")
    }

def generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance labels based on the given compliance configuration.

    Args:
        compliance_config (ComplianceConfig): The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance labels.
    """
    labels = {}
    if compliance_config.fisma.enabled:
        labels['compliance.fisma.enabled'] = 'true'
    if compliance_config.nist.enabled:
        labels['compliance.nist.enabled'] = 'true'
    if compliance_config.scip.environment:
        labels['compliance.scip.environment'] = sanitize_label_value(compliance_config.scip.environment)
    return labels

def generate_compliance_annotations(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance annotations based on the given compliance configuration.

    Args:
        compliance_config (ComplianceConfig): The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance annotations.
    """

    # TODO: enhance if logic to improve efficiency, DRY, readability and maintainability
    annotations = {}
    if compliance_config.fisma.level:
        annotations['compliance.fisma.level'] = compliance_config.fisma.level
    if compliance_config.fisma.ato:
        annotations['compliance.fisma.ato'] = json.dumps(compliance_config.fisma.ato)
    if compliance_config.nist.controls:
        annotations['compliance.nist.controls'] = json.dumps(compliance_config.nist.controls)
    if compliance_config.nist.auxiliary:
        annotations['compliance.nist.auxiliary'] = json.dumps(compliance_config.nist.auxiliary)
    if compliance_config.nist.exceptions:
        annotations['compliance.nist.exceptions'] = json.dumps(compliance_config.nist.exceptions)
    return annotations

# Function to sanitize a label value to comply with Kubernetes `label` naming conventions
# https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
# TODO:
# - retool this feature as a more efficient implementation in `collect_git_info()` and related functions.
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
