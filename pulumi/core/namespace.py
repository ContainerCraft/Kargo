# ./pulumi/core/namespace.py
# Description:

import pulumi
import pulumi_kubernetes as k8s
from typing import List, Optional
from .types import NamespaceConfig

def create_namespace(
    config: NamespaceConfig,
    k8s_provider: k8s.Provider,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.core.v1.Namespace:
    """
    Creates a Kubernetes namespace with the provided configuration.

    Args:
        config (NamespaceConfig): The configuration object for the namespace.
        k8s_provider (k8s.Provider): The Kubernetes provider.
        depends_on (Optional[List[pulumi.Resource]]): List of resources this namespace depends on.

    Returns:
        k8s.core.v1.Namespace: The created namespace resource.
    """
    if depends_on is None:
        depends_on = []

    namespace_resource = k8s.core.v1.Namespace(
        config.name,
        metadata={
            "name": config.name,
            "labels": config.labels,
            "annotations": config.annotations,
        },
        spec={
            "finalizers": config.finalizers,
        },
        opts=pulumi.ResourceOptions(
            protect=config.protect,
            retain_on_delete=config.retain_on_delete,
            provider=k8s_provider,
            depends_on=depends_on,
            ignore_changes=config.ignore_changes,
            custom_timeouts=pulumi.CustomTimeouts(
                create=config.custom_timeouts.get("create", "5m"),
                update=config.custom_timeouts.get("update", "10m"),
                delete=config.custom_timeouts.get("delete", "10m"),
            ),
        ),
    )

    return namespace_resource
