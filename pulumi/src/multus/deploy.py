import pulumi
import pulumi_kubernetes as k8s


def transform_resources(obj):
    """
    Transform Kubernetes resource objects:
    - Update hostPath mounts for netns
    - Set standardized resource requests/limits
    - Add clean exit for multus-shim copy command

    Args:
        obj: The kubernetes resource object to transform

    Returns:
        Modified resource object
    """
    pulumi.log.debug(f"Object keys: {list(obj.keys())}")

    if (
        obj.get("kind", "") == "DaemonSet"
        and obj.get("metadata", {}).get("name", "") == "kube-multus-ds"
    ):
        if "spec" in obj:
            pod_spec = obj["spec"]["template"]["spec"]

            # Transform main container (kube-multus)
            for container in pod_spec.get("containers", []):
                if container.get("name") == "kube-multus":
                    if "resources" not in container:
                        container["resources"] = {}

                    # Set standardized resource limits/requests
                    container["resources"] = {
                        "requests": {"cpu": "10m", "memory": "60Mi"},
                        "limits": {"cpu": "500m", "memory": "3Gi"},
                    }

            # Transform init containers
            init_containers = pod_spec.get("initContainers", [])
            for init_container in init_containers:
                # Set resources for install-multus-binary container
                if init_container.get("name") == "install-multus-binary":
                    # Update resource limits/requests
                    init_container["resources"] = {
                        "requests": {"cpu": "10m", "memory": "60Mi"},
                        "limits": {"cpu": "500m", "memory": "3Gi"},
                    }

                    # Add clean exit for multus-shim copy command
                    # Workaround: Adding '| true' ensures clean container exit even if copy fails
                    # This is temporary until upstream provides more robust shim installation
                    init_container["command"] = [
                        "sh",
                        "-c",
                        "cp -f /usr/src/multus-cni/bin/multus-shim /host/opt/cni/bin/multus-shim || true",
                    ]

                # Set resources for install-cni container
                elif init_container.get("name") == "install-cni":
                    init_container["resources"] = {
                        "requests": {"cpu": "10m", "memory": "60Mi"},
                        "limits": {"cpu": "500m", "memory": "3Gi"},
                    }

            # Transform volume paths
            volumes = pod_spec.get("volumes", [])
            for vol in volumes:
                if "hostPath" in vol:
                    current_path = vol["hostPath"].get("path", "").rstrip("/")
                    if current_path == "/run/netns":
                        vol["hostPath"]["path"] = "/var/run/netns"

    return obj


def deploy_multus(depends, version, bridge_name, k8s_provider):
    """
    Deploy Multus CNI with Talos-specific configuration

    Args:
        depends: List of resources this deployment depends on
        version: Multus CNI version to deploy
        bridge_name: Name of bridge interface to configure
        k8s_provider: Kubernetes provider instance

    Returns:
        Tuple containing:
        - Multus version deployed
        - Multus deployment resources
    """
    resource_name = f"k8snetworkplumbingwg-multus-daemonset-thick"
    manifest_url = f"https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/{version}/deployments/multus-daemonset-thick.yml"

    daemonset_patch = {
        "apiVersion": "apps/v1",
        "kind": "DaemonSet",
        "metadata": {"name": "kube-multus-ds", "namespace": "kube-system"},
        "spec": {
            "template": {
                "spec": {
                    "initContainers": [
                        {
                            "name": "install-cni",
                            "image": "ghcr.io/siderolabs/install-cni:v1.9.0",
                            "command": ["/install-cni.sh"],
                            "securityContext": {"privileged": True},
                            "volumeMounts": [
                                {
                                    "name": "cnibin",
                                    "mountPath": "/host/opt/cni/bin",
                                    "mountPropagation": "Bidirectional",
                                }
                            ],
                        }
                    ]
                }
            }
        },
    }

    multus = k8s.yaml.ConfigFile(
        resource_name,
        file=manifest_url,
        transformations=[transform_resources],
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    k8s.apps.v1.DaemonSetPatch(
        "multus-daemonset-patch",
        metadata={"name": "kube-multus-ds", "namespace": "kube-system"},
        spec=daemonset_patch["spec"],
        opts=pulumi.ResourceOptions(depends_on=[multus]),
    )

    network_attachment_definition = k8s.apiextensions.CustomResource(
        "kargo-net-attach-def",
        api_version="k8s.cni.cncf.io/v1",
        kind="NetworkAttachmentDefinition",
        metadata={"name": f"{bridge_name}", "namespace": "default"},
        spec={
            "config": pulumi.Output.all(bridge_name, bridge_name).apply(
                lambda args: f"""
            {{
                "cniVersion": "0.3.1",
                "name": "{bridge_name}",
                "plugins": [
                    {{
                        "type": "bridge",
                        "bridge": "{bridge_name}",
                        "ipam": {{}}
                    }},
                    {{
                        "type": "tuning"
                    }}
                ]
            }}"""
            )
        },
        opts=pulumi.ResourceOptions(
            depends_on=multus,
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="5m", update="5m", delete="5m"
            ),
        ),
    )

    pulumi.export(
        "network_attachment_definition", network_attachment_definition.metadata["name"]
    )

    return "master", multus
