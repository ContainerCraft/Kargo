import pulumi
from pulumi_kubernetes import core, meta, Provider

class KubernetesApiEndpointIp(pulumi.ComponentResource):
    """
    Represents a Kubernetes API endpoint IP address.

    Args:
        name (str): The name of the resource.
        k8s_provider (Provider): The Kubernetes provider.

    Attributes:
        endpoint (core.v1.Endpoints): The Kubernetes endpoint.
        ips (pulumi.Output[str]): The comma-separated string of IP addresses.

    """
    def __init__(self, name: str, k8s_provider: Provider):
        super().__init__('custom:x:KubernetesApiEndpointIp', name, {}, opts=pulumi.ResourceOptions(provider=k8s_provider))

        self.endpoint = core.v1.Endpoints.get(
            "kubernetes",
            "kubernetes",
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

        self.ips = self.endpoint.subsets.apply(
            lambda subsets: ','.join([address.ip for subset in subsets for address in subset.addresses]) if subsets else ''
        )

        self.register_outputs({"ip_string": self.ips})
