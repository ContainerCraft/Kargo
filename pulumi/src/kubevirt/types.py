# src/kubevirt/types.py

import pulumi
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class KubeVirtConfig:
    """
    Configuration for deploying the KubeVirt module.

    Attributes:
        namespace (str): The Kubernetes namespace where KubeVirt will be deployed.
            Defaults to "kubevirt".
        version (Optional[str]): The version of KubeVirt to deploy.
            Defaults to None, which fetches the latest version.
        use_emulation (bool): Whether to use emulation for KVM.
            Defaults to False.
    """
    namespace: str = "kubevirt"
    version: Optional[str] = None
    use_emulation: bool = False

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'KubeVirtConfig':
        """
        Merges user-provided configuration with default values.

        Args:
            user_config (Dict[str, Any]): A dictionary containing user-provided configuration options.

        Returns:
            KubeVirtConfig: An instance of KubeVirtConfig with merged settings.
        """
        default_config = KubeVirtConfig()
        merged_config = default_config.__dict__.copy()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                merged_config[key] = value
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in kubevirt config.")
        return KubeVirtConfig(**merged_config)
