import pulumi
import pulumi_kubernetes as k8s

def create_namespace(
        depends,
        ns_name: str,
        ns_retain,
        ns_protect,
        k8s_provider: k8s.Provider,
        custom_labels=None,
        custom_annotations=None,
        finalizers=None
    ):
    # Default labels and annotations
    default_labels = {
        "ccio.v1/app": "kargo"
    }
    default_annotations = {}

    # Merge custom labels and annotations with defaults
    complete_labels = {**default_labels, **(custom_labels or {})}
    complete_annotations = {**default_annotations, **(custom_annotations or {})}

    # Use default finalizers if none are provided
    if finalizers is None:
        finalizers = ["kubernetes"]

    # Create the namespace with merged labels, annotations, and finalizers
    namespace_resource = k8s.core.v1.Namespace(
        ns_name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=ns_name,
            annotations=complete_annotations,
            labels=complete_labels
        ),
        spec=k8s.core.v1.NamespaceSpecArgs(
            finalizers=finalizers,
        ),
        opts=pulumi.ResourceOptions(
            protect=ns_protect,
            retain_on_delete=ns_retain,
            provider=k8s_provider,
            depends_on=depends,
            ignore_changes=[
                "metadata",
                "spec"
            ],
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m",
                update="10m",
                delete="10m"
            )
        )
    )

    return namespace_resource
