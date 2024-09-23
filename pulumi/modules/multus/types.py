# pulumi/modules/multus/types.py

"""
Defines the data structure for the Multus module configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi

@dataclass
class MultusConfig:
    version: str = "master"
    namespace: str = "multus"
    bridge_name: str = "br0"
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'MultusConfig':
        default_config = MultusConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in multus config.")
        return default_config
