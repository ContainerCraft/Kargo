import pulumi
import pulumi_kubernetes as k8s

def create_namespace(
        ns_name: str,
        ns_retain,
        ns_protect,
        k8s_provider: k8s.Provider
    ):

    namespace_resource = k8s.core.v1.Namespace(
        ns_name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=ns_name,
            annotations={},
            labels={
                "ccio.v1/app": "kargo"
            }
        ),
        spec=k8s.core.v1.NamespaceSpecArgs(
            finalizers=["kubernetes"],
        ),
        opts=pulumi.ResourceOptions(
            protect=ns_protect,
            retain_on_delete=ns_retain,
            provider=k8s_provider,
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
