# ./pulumi/modules/kubevirt/types.py
# Description:

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

import pulumi
from core.metadata import get_global_labels, get_global_annotations

@dataclass
class KubeVirtConfig:
    namespace: str = "kubevirt"
    version: Optional[str] = None
    use_emulation: bool = False
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> 'KubeVirtConfig':
        default_config = cls()
        merged_config = default_config.__dict__.copy()

        for key, value in user_config.items():
            if hasattr(default_config, key):
                merged_config[key] = value
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in kubevirt config.")

        global_labels = get_global_labels()
        global_annotations = get_global_annotations()

        merged_config['labels'].update(global_labels)
        merged_config['annotations'].update(global_annotations)

        return cls(**merged_config)
