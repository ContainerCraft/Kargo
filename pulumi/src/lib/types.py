# src/lib/types.py

"""
Types and data structures used across Kargo modules.

This module defines shared configuration types that are utilized by various modules
within the Kargo PaaS platform. These data classes help standardize configurations
and simplify the management of Kubernetes resources.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class NamespaceConfig:
    """
    Configuration for creating or managing a Kubernetes namespace.

    Attributes:
        name (str): The name of the Kubernetes namespace.
        labels (Dict[str, str]): Labels to apply to the namespace for identification and grouping.
            Defaults to {"ccio.v1/app": "kargo"}.
        annotations (Dict[str, str]): Annotations to add metadata to the namespace.
            Defaults to an empty dictionary.
        finalizers (List[str]): List of finalizers to prevent accidental deletion of the namespace.
            Defaults to ["kubernetes"].
        protect (bool): If True, protects the namespace from deletion.
            Defaults to False.
        retain_on_delete (bool): If True, retains the namespace when the Pulumi stack is destroyed.
            Defaults to False.
        ignore_changes (List[str]): Fields to ignore during updates, useful for fields managed externally.
            Defaults to ["metadata", "spec"].
        custom_timeouts (Dict[str, str]): Custom timeouts for create, update, and delete operations.
            Helps manage operations that may take longer than default timeouts.
            Defaults to {"create": "5m", "update": "10m", "delete": "10m"}.
    """
    name: str
    labels: Dict[str, str] = field(default_factory=lambda: {"ccio.v1/app": "kargo"})
    annotations: Dict[str, str] = field(default_factory=dict)
    finalizers: List[str] = field(default_factory=lambda: ["kubernetes"])
    protect: bool = False
    retain_on_delete: bool = False
    ignore_changes: List[str] = field(default_factory=lambda: ["metadata", "spec"])
    custom_timeouts: Dict[str, str] = field(default_factory=lambda: {
        "create": "5m",
        "update": "10m",
        "delete": "10m"
    })
