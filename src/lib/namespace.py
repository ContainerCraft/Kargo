import pulumi
from pulumi_kubernetes import core as k8s_core, meta as k8s_meta
from typing import List

def create_namespaces(namespaces: List[str], provider):
    """
    Create Kubernetes namespaces.

    Args:
        namespaces (List[str]): List of namespace names.
        provider: The provider for the namespaces.

    Returns:
        List[k8s_core.v1.Namespace]: List of created namespace objects.
    """
    namespace_objects = []
    for ns_name in namespaces:
        ns = k8s_core.v1.Namespace(
            ns_name,
            metadata=k8s_meta.v1.ObjectMetaArgs(name=ns_name),
            opts=pulumi.ResourceOptions(provider=provider)
        )
        namespace_objects.append(ns)
    return namespace_objects
