# pulumi/modules/hostpath_provisioner/deploy.py

import requests
import pulumi
import pulumi_kubernetes as k8s
from typing import List, Dict, Any, Tuple, Optional
from core.resource_helpers import create_namespace, create_custom_resource, create_config_file
from core.utils import wait_for_crds
from .types import HostPathProvisionerConfig


def deploy_hostpath_provisioner_module(
    config_hostpath_provisioner: HostPathProvisionerConfig,
    global_depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
) -> Tuple[str, k8s.yaml.ConfigFile]:
    """
    Deploys the HostPath Provisioner module and returns the version and the deployed resource.

    Args:
        config_hostpath_provisioner (HostPathProvisionerConfig): Configuration for the HostPath Provisioner.
        global_depends_on (List[pulumi.Resource]): Global dependencies for all modules.
        k8s_provider (k8s.Provider): The Kubernetes provider.

    Returns:
        Tuple[str, k8s.yaml.ConfigFile]: The version deployed and the configured webhook resource.
    """
    hostpath_version, hostpath_resource = deploy_hostpath_provisioner(
        config_hostpath_provisioner=config_hostpath_provisioner,
        depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Update global dependencies
    global_depends_on.append(hostpath_resource)

    return hostpath_version, hostpath_resource


def deploy_hostpath_provisioner(
    config_hostpath_provisioner: HostPathProvisionerConfig,
    depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
) -> Tuple[str, k8s.yaml.ConfigFile]:
    """
    Deploys the HostPath Provisioner and related resources.

    Args:
        config_hostpath_provisioner (HostPathProvisionerConfig): Configuration for the HostPath Provisioner.
        depends_on (List[pulumi.Resource]): Dependencies for this deployment.
        k8s_provider (k8s.Provider): The Kubernetes provider.

    Returns:
        Tuple[str, k8s.yaml.ConfigFile]: The version deployed and the configured webhook resource.
    """
    name = "hostpath-provisioner"
    namespace = config_hostpath_provisioner.namespace

    namespace_resource = create_namespace(
        name=namespace,
        labels=config_hostpath_provisioner.labels,
        annotations=config_hostpath_provisioner.annotations,
        k8s_provider=k8s_provider,
        parent=k8s_provider,
        depends_on=depends_on,
    )

    # Determine version to use
    version = get_latest_version() if config_hostpath_provisioner.version == "latest" else config_hostpath_provisioner.version

    def enforce_namespace(resource_args: pulumi.ResourceTransformationArgs) -> pulumi.ResourceTransformationResult:
        """
        Transformation function to enforce namespace on all resources.
        """
        props = resource_args.props
        namespace_conflict = False

        # Handle ObjectMetaArgs case
        if isinstance(props.get('metadata'), k8s.meta.v1.ObjectMetaArgs):
            meta = props['metadata']
            if meta.namespace and meta.namespace != namespace:
                namespace_conflict = True
            updated_meta = k8s.meta.v1.ObjectMetaArgs(
                name=meta.name,
                namespace=namespace,
                labels=meta.labels,
                annotations=meta.annotations
            )
            props['metadata'] = updated_meta

        # Handle dictionary style metadata
        elif isinstance(props.get('metadata'), dict):
            meta = props['metadata']
            if 'namespace' in meta and meta['namespace'] != namespace:
                namespace_conflict = True
            meta['namespace'] = namespace

        if namespace_conflict:
            raise ValueError("Resource namespace conflict detected.")

        return pulumi.ResourceTransformationResult(props, resource_args.opts)

    # Deploy the webhook
    webhook_url = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/webhook.yaml'
    webhook = create_config_file(
        name="hostpath-provisioner-webhook",
        file=webhook_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=namespace_resource,
            depends_on=depends_on,
            custom_timeouts=pulumi.CustomTimeouts(create="10m", update="5m", delete="5m"),
            transformations=[enforce_namespace]
        ),
    )

    # Deploy the operator
    operator_url = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/operator.yaml'
    operator = create_config_file(
        name="hostpath-provisioner-operator",
        file=operator_url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            parent=webhook,
            depends_on=depends_on,
            custom_timeouts=pulumi.CustomTimeouts(create="10m", update="5m", delete="5m"),
            transformations=[enforce_namespace]
        ),
    )

    # Ensure CRDs are created before HostPathProvisioner resource
    crds = wait_for_crds(
        crd_names=["hostpathprovisioners.hostpathprovisioner.kubevirt.io"],
        k8s_provider=k8s_provider,
        depends_on=depends_on,
        parent=operator,
    )

    # Create HostPathProvisioner resource
    hostpath_provisioner = create_custom_resource(
        name="hostpath-provisioner",
        args={
            "apiVersion": "hostpathprovisioner.kubevirt.io/v1beta1",
            "kind": "HostPathProvisioner",
            "metadata": {
                "name": "hostpath-provisioner",
                "namespace": namespace,
            },
            "spec": {
                "imagePullPolicy": "IfNotPresent",
                "storagePools": [{
                    "name": "ssd",
                    "path": config_hostpath_provisioner.hostpath,
                }],
                "workload": {
                    "nodeSelector": {
                        "kubernetes.io/os": "linux"
                    }
                }
            },
        },
        opts=pulumi.ResourceOptions(
            parent=operator,
            depends_on=depends_on + crds,
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(create="10m", update="5m", delete="5m")
        ),
    )

    # Define the StorageClass
    storage_class = create_storage_class(
        name="hostpath-storage-class-ssd",
        provisioner="kubevirt.io.hostpath-provisioner",
        namespace=namespace,
        default=config_hostpath_provisioner.default,
        storage_pool="ssd",
        parent=hostpath_provisioner,
        k8s_provider=k8s_provider,
    )

    return version, webhook


def get_latest_version() -> str:
    """
    Retrieves the latest stable version of HostPath Provisioner.

    Returns:
        str: The latest version number.
    """
    try:
        tag_url = 'https://github.com/kubevirt/hostpath-provisioner-operator/releases/latest'
        response = requests.get(tag_url, allow_redirects=False)
        final_url = response.headers.get('location')
        version = final_url.split('/')[-1].lstrip('v') if response.status_code == 302 else "0.17.0"
        return version
    except Exception as e:
        pulumi.log.error(f"Error fetching the latest version: {e}")
        return "0.17.0"


def create_storage_class(
    name: str,
    provisioner: str,
    namespace: str,
    default: bool,
    storage_pool: str,
    parent: pulumi.Resource,
    k8s_provider: k8s.Provider,
) -> k8s.storage.v1.StorageClass:
    """
    Creates a StorageClass resource specific to HostPath Provisioner.

    Args:
        name (str): The name of the storage class.
        provisioner (str): The provisioner to use.
        namespace (str): The namespace to deploy into.
        default (bool): Whether this storage class should be the default.
        storage_pool (str): The name of the storage pool.
        parent (pulumi.Resource): The parent resource.
        k8s_provider (k8s.Provider): The Kubernetes provider.

    Returns:
        k8s.storage.v1.StorageClass: The created StorageClass resource.
    """
    if default:
        is_default_storage_class = "true"
    else:
        is_default_storage_class = "false"

    return k8s.storage.v1.StorageClass(
        resource_name=name,
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            annotations={
                "storageclass.kubernetes.io/is-default-class": is_default_storage_class,
            },
        ),
        provisioner=provisioner,
        reclaim_policy="Delete",
        volume_binding_mode="WaitForFirstConsumer",
        parameters={
            "storagePool": storage_pool,
        },
        opts=pulumi.ResourceOptions(
            parent=parent,
            provider=k8s_provider,
            custom_timeouts=pulumi.CustomTimeouts(create="5m", update="5m", delete="5m")
        ),
    )
