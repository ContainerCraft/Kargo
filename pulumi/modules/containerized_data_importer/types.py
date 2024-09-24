# pulumi/modules/containerized_data_importer/types.py

"""
Defines the data structure for the Containerized Data Importer (CDI) module configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class CdiConfig:
    version: Optional[str] = "latest"
    namespace: str = "cdi"
    labels: Dict[str, str] = field(default_factory=lambda: {"app": "cdi"})
    annotations: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'CdiConfig':
        default_config = CdiConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in cdi config.")
        return default_config
