import requests
import pulumi
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.storage.v1 import StorageClass
from src.lib.namespace import create_namespace


def deploy(
    depends: pulumi.Output[list],
    version: str,
    ns_name: str,
    hostpath: str,
    default: bool,
    k8s_provider: k8s.Provider,
):

    # If version is not supplied, fetch the latest stable version
    if version is None:
        tag_url = (
            "https://github.com/kubevirt/hostpath-provisioner-operator/releases/latest"
        )
        tag = requests.get(tag_url, allow_redirects=False).headers.get("location")
        version = tag.split("/")[-1] if tag else "0.17.0"
        version = version.lstrip("v")
        pulumi.log.info(
            f"Setting helm release version to latest stable: hostpath-provisioner/{version}"
        )
    else:
        pulumi.log.info(f"Using helm release version: hostpath-provisioner/{version}")

    # Create namespace
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubevirt.io": "",
        "kubernetes.io/metadata.name": ns_name,
        "pod-security.kubernetes.io/enforce": "privileged",
    }
    namespace = create_namespace(
        depends, ns_name, ns_retain, ns_protect, k8s_provider, ns_labels, ns_annotations
    )

    # Create Role for pod access within the namespace
    pod_reader_role = k8s.rbac.v1.Role(
        "hostpath-provisioner-pod-reader",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="hostpath-provisioner-pod-reader",
            namespace=ns_name
        ),
        rules=[
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["pods"],
                verbs=["get", "watch", "list"]
            )
        ],
        opts=pulumi.ResourceOptions(
            parent=namespace,
            provider=k8s_provider
        )
    )

    # Create RoleBinding for pod reader role
    pod_reader_binding = k8s.rbac.v1.RoleBinding(
        "hostpath-provisioner-pod-reader-binding",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="hostpath-provisioner-pod-reader-binding",
            namespace=ns_name
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind="ServiceAccount",
                name="hostpath-provisioner-admin-csi",
                namespace=ns_name
            )
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name="hostpath-provisioner-pod-reader"
        ),
        opts=pulumi.ResourceOptions(
            parent=pod_reader_role,
            provider=k8s_provider
        )
    )

    # Create ClusterRole for CSI storage capacities management
    csi_storage_role = k8s.rbac.v1.ClusterRole(
        "hostpath-provisioner-csi-storage",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="hostpath-provisioner-csi-storage"
        ),
        rules=[
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=["storage.k8s.io"],
                resources=["csistoragecapacities"],
                verbs=["get", "list", "watch", "create", "update", "patch", "delete"]
            )
        ],
        opts=pulumi.ResourceOptions(
            parent=namespace,
            provider=k8s_provider
        )
    )

    # Create ClusterRoleBinding for CSI storage role
    csi_storage_binding = k8s.rbac.v1.ClusterRoleBinding(
        "hostpath-provisioner-csi-storage-binding",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="hostpath-provisioner-csi-storage-binding"
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind="ServiceAccount",
                name="hostpath-provisioner-admin-csi",
                namespace=ns_name
            )
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="hostpath-provisioner-csi-storage"
        ),
        opts=pulumi.ResourceOptions(
            parent=csi_storage_role,
            provider=k8s_provider
        )
    )

    # Function to add namespace to resource if not set
    def add_namespace(args):
        obj = args.props

        if "metadata" in obj:
            if isinstance(obj["metadata"], ObjectMetaArgs):
                if not obj["metadata"].namespace:
                    obj["metadata"].namespace = ns_name
            else:
                if obj["metadata"] is None:
                    obj["metadata"] = {}
                if not obj["metadata"].get("namespace"):
                    obj["metadata"]["namespace"] = ns_name
        else:
            obj["metadata"] = {"namespace": ns_name}

        # Return the modified object wrapped in ResourceTransformationResult
        return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)

    # Deploy the webhook
    url_webhook = f"https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/webhook.yaml"
    webhook = k8s.yaml.ConfigFile(
        "hostpath-provisioner-webhook",
        file=url_webhook,
        opts=ResourceOptions(
            parent=namespace,
            depends_on=[pod_reader_binding, csi_storage_binding],
            provider=k8s_provider,
            transformations=[add_namespace],
            custom_timeouts=pulumi.CustomTimeouts(
                create="1m", update="1m", delete="1m"
            ),
        ),
    )

    # Deploy the operator with a namespace transformation
    url_operator = f"https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/operator.yaml"
    operator = k8s.yaml.ConfigFile(
        "hostpath-provisioner-operator",
        file=url_operator,
        opts=ResourceOptions(
            parent=namespace,
            depends_on=[webhook],
            provider=k8s_provider,
            transformations=[add_namespace],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    # Ensure the CRDs are created before the HostPathProvisioner resource
    # TODO: solve for the case where child resources are created before parent exists
    crd = k8s.apiextensions.v1.CustomResourceDefinition.get(
        "hostpathprovisioners",
        id="hostpathprovisioners.hostpathprovisioner.kubevirt.io",
        opts=ResourceOptions(
            parent=namespace,
            depends_on=[operator],
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="9m", update="9m", delete="2m"
            ),
        ),
    )

    # Create a HostPathProvisioner resource
    hostpath_provisioner = CustomResource(
        "hostpath-provisioner-hpp",
        api_version="hostpathprovisioner.kubevirt.io/v1beta1",
        kind="HostPathProvisioner",
        metadata={"name": "hostpath-provisioner-class-ssd", "namespace": ns_name},
        spec={
            "imagePullPolicy": "IfNotPresent",
            "storagePools": [{"name": "ssd", "path": hostpath}],
            "workload": {"nodeSelector": {"kubernetes.io/os": "linux"}},
        },
        opts=pulumi.ResourceOptions(
            parent=namespace,
            depends_on=[crd],
            provider=k8s_provider,
            ignore_changes=["status"],
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    # Define the StorageClass
    storage_class = StorageClass(
        "hostpath-storage-class-ssd",
        metadata=ObjectMetaArgs(
            name="ssd",
            annotations={
                "storageclass.kubernetes.io/is-default-class": (
                    "true" if default else "false"
                )
            },
        ),
        reclaim_policy="Delete",
        provisioner="kubevirt.io.hostpath-provisioner",
        volume_binding_mode="Immediate",
        parameters={
            "storagePool": "ssd",
        },
        opts=ResourceOptions(
            parent=namespace,
            depends_on=[hostpath_provisioner],
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(
                create="8m", update="8m", delete="2m"
            ),
        ),
    )

    return version, webhook  # operator
