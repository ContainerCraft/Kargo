# pulumi/modules/prometheus/types.py

"""
Defines the data structure for the Prometheus module configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class PrometheusConfig:
    version: Optional[str] = None
    namespace: str = "monitoring"
    openunison_enabled: bool = False
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'PrometheusConfig':
        default_config = PrometheusConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in prometheus config.")
        return default_config
