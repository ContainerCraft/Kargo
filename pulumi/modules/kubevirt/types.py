# modules/kubevirt/types.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi
from core.metadata import get_global_labels, get_global_annotations

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
        labels (Dict[str, str]): Labels to apply to KubeVirt resources.
            Defaults to an empty dict.
        annotations (Dict[str, Any]): Annotations to apply to KubeVirt resources.
            Defaults to an empty dict.
    """
    namespace: str = "kubevirt"
    version: Optional[str] = None
    use_emulation: bool = False
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'KubeVirtConfig':
        """
        Merges user-provided configuration with default values and global labels and annotations.

        Args:
            user_config (Dict[str, Any]): A dictionary containing user-provided configuration options.

        Returns:
            KubeVirtConfig: An instance of KubeVirtConfig with merged settings.
        """
        default_config = KubeVirtConfig()
        merged_config = default_config.__dict__.copy()

        # Merge user-provided config
        for key, value in user_config.items():
            if hasattr(default_config, key):
                merged_config[key] = value
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in kubevirt config.")

        # Retrieve global labels and annotations
        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

        # Merge global labels and annotations into the config
        merged_config['labels'].update(global_labels)
        merged_config['annotations'].update(global_annotations)

        return KubeVirtConfig(**merged_config)
