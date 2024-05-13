import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.core.v1 import Namespace, ObjectMetaArgs

def create_namespace(
        namespace: str,
        provider: k8s.Provider,
        ns_retain: bool,
        ns_protect: bool
    ):

    namespace_resource = k8s.core.v1.Namespace(
        "cert-manager-namespace",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=namespace
            #annotations={},
            #labels={
            #    "ccio.v1/app": "kargo"
            #}
        ),
        #spec=k8s.core.v1.NamespaceSpecArgs(
        #    finalizers=["kubernetes"],
        #),
        opts=pulumi.ResourceOptions(
            provider=provider,
            protect=ns_protect,
            retain_on_delete=ns_retain,
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
