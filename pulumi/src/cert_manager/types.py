# src/cert_manager/types.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi

@dataclass
class CertManagerConfig:
    namespace: str = "cert-manager"
    version: Optional[str] = None
    cluster_issuer: str = "cluster-selfsigned-issuer"
    install_crds: bool = True

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
        """
        Merges user-provided configuration with default values for CertManagerConfig.

        Args:
            user_config: The user-provided configuration dictionary.

        Returns:
            A CertManagerConfig object with defaults applied.
        """
        default_config = CertManagerConfig()
        merged_config = default_config.__dict__.copy()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                merged_config[key] = value
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in cert_manager config.")
        return CertManagerConfig(**merged_config)
