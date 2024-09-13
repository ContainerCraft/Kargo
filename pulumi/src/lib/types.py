# src/lib/types.py

from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class NamespaceConfig:
    name: str
    labels: Dict[str, str] = field(default_factory=lambda: {"ccio.v1/app": "kargo"})
    annotations: Dict[str, str] = field(default_factory=dict)
    finalizers: List[str] = field(default_factory=lambda: ["kubernetes"])
    protect: bool = False
    retain_on_delete: bool = False
    ignore_changes: List[str] = field(default_factory=lambda: ["metadata", "spec"])
    custom_timeouts: Dict[str, str] = field(default_factory=lambda: {"create": "5m", "update": "10m", "delete": "10m"})
