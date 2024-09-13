# src/lib/namespace.py

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
    Creates a Kubernetes Namespace based on the provided configuration.

    Args:
        config: NamespaceConfig object containing namespace configurations.
        k8s_provider: The Kubernetes provider.
        depends_on: Optional list of resources to depend on.

    Returns:
        The created Namespace resource.
    """

    # Ensure depends_on is a list
    if depends_on is None:
        depends_on = []

    # Create the namespace
    namespace_resource = k8s.core.v1.Namespace(
        config.name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=config.name,
            labels=config.labels,
            annotations=config.annotations,
        ),
        spec=k8s.core.v1.NamespaceSpecArgs(
            finalizers=config.finalizers,
        ),
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
        )
    )

    return namespace_resource
