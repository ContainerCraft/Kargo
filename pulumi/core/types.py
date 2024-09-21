# pulumi/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across modules
within the Kargo PaaS platform.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class NamespaceConfig:
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

@dataclass
class FismaConfig:
    enabled: bool = False
    level: Optional[str] = None
    ato: Dict[str, str] = field(default_factory=dict)

@dataclass
class NistConfig:
    enabled: bool = False
    controls: List[str] = field(default_factory=list)
    auxiliary: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)

@dataclass
class ScipConfig:
    environment: Optional[str] = None
    ownership: Dict[str, Any] = field(default_factory=dict)
    provider: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceConfig:
    fisma: FismaConfig = field(default_factory=FismaConfig)
    nist: NistConfig = field(default_factory=NistConfig)
    scip: ScipConfig = field(default_factory=ScipConfig)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'ComplianceConfig':
        """
        Merges user-provided compliance configuration with default configuration.

        Args:
            user_config (Dict[str, Any]): The user-provided compliance configuration.

        Returns:
            ComplianceConfig: The merged compliance configuration object.
        """
        default_config = ComplianceConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                nested_config = getattr(default_config, key)
                for nested_key, nested_value in value.items():
                    if hasattr(nested_config, nested_key):
                        setattr(nested_config, nested_key, nested_value)
                    else:
                        pulumi.log.warn(f"Unknown key '{nested_key}' in compliance.{key}")
            else:
                pulumi.log.warn(f"Unknown compliance configuration key: {key}")
        return default_config
