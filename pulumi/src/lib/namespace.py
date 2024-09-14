# src/lib/namespace.py

"""
Utility functions for managing Kubernetes namespaces within the Kargo PaaS platform.

This module provides functions to create and manage Kubernetes namespaces
using Pulumi and the Kubernetes provider. It leverages the NamespaceConfig
data class to standardize configurations and ensure consistency across deployments.
"""

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

    This function simplifies the creation of a Kubernetes namespace by applying
    settings specified in a NamespaceConfig object. It ensures namespaces are
    created consistently and according to best practices within the Kargo PaaS platform.

    Args:
        config (NamespaceConfig): An object containing namespace configuration settings.
        k8s_provider (k8s.Provider): The Kubernetes provider instance to interact with the cluster.
        depends_on (Optional[List[pulumi.Resource]]): An optional list of resources that
            this namespace depends on, ensuring proper resource creation order.

    Returns:
        k8s.core.v1.Namespace: The created Namespace resource.

    Example:
        ```python
        # Define namespace configuration
        namespace_config = NamespaceConfig(
            name="my-namespace",
            labels={"app": "my-app"},
            protect=True
        )

        # Create the namespace
        namespace_resource = create_namespace(
            config=namespace_config,
            k8s_provider=k8s_provider,
            depends_on=[other_resource],
        )
        ```
    """
    # Ensure depends_on is initialized as a list if not provided
    if depends_on is None:
        depends_on = []

    # Create the Kubernetes Namespace resource with the specified configuration
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
