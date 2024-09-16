# src/cert_manager/types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
import pulumi

@dataclass
class CertManagerConfig:
    version: Optional[str] = None
    namespace: str = "cert-manager"
    cluster_issuer: str = "cluster-selfsigned-issuer"
    install_crds: bool = True

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
        default_config = CertManagerConfig()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in cert_manager config.")
        return default_config
