# pulumi/modules/hostpath_provisioner/types.py

"""
Defines the data structure for the HostPath Provisioner module configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi

@dataclass
class HostPathProvisionerConfig:
    version: Optional[str] = "latest"
    namespace: str = "hostpath-provisioner"
    hostpath: str = "/var/lib/hostpath-provisioner"
    default: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'HostPathProvisionerConfig':
        default_config = HostPathProvisionerConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in hostpath_provisioner config.")
        return default_config
