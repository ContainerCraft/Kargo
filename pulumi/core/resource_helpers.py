# pulumi/core/resource_helpers.py

import pulumi
import pulumi_kubernetes as k8s
from typing import Optional, Dict, Any, List, Callable
from .metadata import get_global_labels, get_global_annotations
from .utils import set_resource_metadata
from .types import NamespaceConfig

def create_namespace(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    finalizers: Optional[List[str]] = None,
    custom_timeouts: Optional[Dict[str, str]] = None,
    opts: Optional[pulumi.ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.core.v1.Namespace:
    """
    Creates a Kubernetes Namespace with global labels and annotations.

    Args:
        name (str): The name of the namespace.
        labels (Optional[Dict[str, str]]): Additional labels to apply.
        annotations (Optional[Dict[str, str]]): Additional annotations to apply.
        finalizers (Optional[List[str]]): Finalizers for the namespace.
        custom_timeouts (Optional[Dict[str, str]]): Custom timeouts for resource operations.
        opts (Optional[pulumi.ResourceOptions]): Pulumi resource options.
        k8s_provider (Optional[k8s.Provider]): Kubernetes provider.
        depends_on (Optional[List[pulumi.Resource]]): Resources this resource depends on.

    Returns:
        k8s.core.v1.Namespace: The created Namespace resource.
    """
    if opts is None:
        opts = pulumi.ResourceOptions()
    if labels is None:
        labels = {}
    if annotations is None:
        annotations = {}
    if custom_timeouts is None:
        custom_timeouts = {}
    if depends_on is None:
        depends_on = []

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()
    labels.update(global_labels)
    annotations.update(global_annotations)

    metadata = {
        "name": name,
        "labels": labels,
        "annotations": annotations,
    }

    spec = {}
    if finalizers:
        spec["finalizers"] = finalizers

    opts = pulumi.ResourceOptions.merge(
        opts,
        pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            custom_timeouts=pulumi.CustomTimeouts(
                create=custom_timeouts.get("create", "5m"),
                update=custom_timeouts.get("update", "10m"),
                delete=custom_timeouts.get("delete", "10m"),
            ),
        ),
    )

    return k8s.core.v1.Namespace(
        name,
        metadata=metadata,
        spec=spec,
        opts=opts,
    )

def create_custom_resource(
    name: str,
    args: Dict[str, Any],
    opts: Optional[pulumi.ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.apiextensions.CustomResource:
    if opts is None:
        opts = pulumi.ResourceOptions()
    if depends_on is None:
        depends_on = []

    if 'kind' not in args or 'apiVersion' not in args:
        raise ValueError("The 'args' dictionary must include 'kind' and 'apiVersion' keys.")

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def custom_resource_transform(resource_args: pulumi.ResourceTransformationArgs):
        props = resource_args.props
        if 'metadata' in props:
            set_resource_metadata(props['metadata'], global_labels, global_annotations)
        return pulumi.ResourceTransformationResult(props, resource_args.opts)

    opts = pulumi.ResourceOptions.merge(
        opts,
        pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            transformations=[custom_resource_transform],
        ),
    )

    # Extract required fields from args
    api_version = args['apiVersion']
    kind = args['kind']
    metadata = args.get('metadata', None)
    spec = args.get('spec', None)

    # Corrected constructor call
    return k8s.apiextensions.CustomResource(
        resource_name=name,
        api_version=api_version,
        kind=kind,
        metadata=metadata,
        spec=spec,
        opts=opts
    )

def create_helm_release(
    name: str,
    args: k8s.helm.v3.ReleaseArgs,
    opts: Optional[pulumi.ResourceOptions] = None,
    transformations: Optional[List[Callable[[pulumi.ResourceTransformationArgs], Optional[pulumi.ResourceTransformationResult]]]] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.helm.v3.Release:
    """
    Creates a Helm Release with global labels and annotations.

    Args:
        name (str): The release name.
        args (k8s.helm.v3.ReleaseArgs): Arguments for the Helm release.
        opts (Optional[pulumi.ResourceOptions]): Pulumi resource options.
        transformations (Optional[List[Callable]]): Additional transformations.
        k8s_provider (Optional[k8s.Provider]): Kubernetes provider.
        depends_on (Optional[List[pulumi.Resource]]): Resources this release depends on.

    Returns:
        k8s.helm.v3.Release: The created Helm release.
    """
    if opts is None:
        opts = pulumi.ResourceOptions()
    if transformations is None:
        transformations = []
    if depends_on is None:
        depends_on = []

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def helm_resource_transform(resource_args: pulumi.ResourceTransformationArgs):
        props = resource_args.props
        if 'metadata' in props:
            set_resource_metadata(props['metadata'], global_labels, global_annotations)
        elif 'spec' in props and isinstance(props['spec'], dict):
            if 'metadata' in props['spec']:
                set_resource_metadata(props['spec']['metadata'], global_labels, global_annotations)
        return pulumi.ResourceTransformationResult(props, resource_args.opts)

    transformations.append(helm_resource_transform)

    opts = pulumi.ResourceOptions.merge(
        opts,
        pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            transformations=transformations,
        ),
    )

    return k8s.helm.v3.Release(name, args, opts=opts)

def create_secret(
    name: str,
    args: Dict[str, Any],
    opts: Optional[pulumi.ResourceOptions] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.core.v1.Secret:
    if opts is None:
        opts = pulumi.ResourceOptions()
    if depends_on is None:
        depends_on = []

    # Merge global labels and annotations (if any)
    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def secret_resource_transform(resource_args: pulumi.ResourceTransformationArgs):
        props = resource_args.props
        if 'metadata' in props:
            set_resource_metadata(props['metadata'], global_labels, global_annotations)
        return pulumi.ResourceTransformationResult(props, resource_args.opts)

    # Merge resource options
    opts = pulumi.ResourceOptions.merge(
        opts,
        pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            transformations=[secret_resource_transform],
        ),
    )

    # Constructor call
    return k8s.core.v1.Secret(name, opts, **args)

def create_config_file(
    name: str,
    file: str,
    opts: Optional[pulumi.ResourceOptions] = None,
    transformations: Optional[List[Callable[[pulumi.ResourceTransformationArgs], Optional[pulumi.ResourceTransformationResult]]]] = None,
    k8s_provider: Optional[k8s.Provider] = None,
    depends_on: Optional[List[pulumi.Resource]] = None,
) -> k8s.yaml.ConfigFile:
    """
    Creates Kubernetes resources from a YAML config file with global labels and annotations.

    Args:
        name (str): The resource name.
        file (str): The path to the YAML file.
        opts (Optional[pulumi.ResourceOptions]): Pulumi resource options.
        transformations (Optional[List[Callable]]): Additional transformations.
        k8s_provider (Optional[k8s.Provider]): Kubernetes provider.
        depends_on (Optional[List[pulumi.Resource]]): Resources these resources depend on.

    Returns:
        k8s.yaml.ConfigFile: The created resources.
    """
    if opts is None:
        opts = pulumi.ResourceOptions()
    if transformations is None:
        transformations = []
    if depends_on is None:
        depends_on = []

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()

    def config_file_transform(resource_args: pulumi.ResourceTransformationArgs):
        props = resource_args.props
        if 'metadata' in props:
            set_resource_metadata(props['metadata'], global_labels, global_annotations)
        elif 'spec' in props and isinstance(props['spec'], dict):
            if 'metadata' in props['spec']:
                set_resource_metadata(props['spec']['metadata'], global_labels, global_annotations)
        return pulumi.ResourceTransformationResult(props, resource_args.opts)

    transformations.append(config_file_transform)

    opts = pulumi.ResourceOptions.merge(
        opts,
        pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=depends_on,
            transformations=transformations,
        ),
    )

    return k8s.yaml.ConfigFile(name, file, opts=opts)

def create_meta_objectmeta(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    annotations: Optional[Dict[str, str]] = None,
    namespace: Optional[str] = None,
    **kwargs,
) -> k8s.meta.v1.ObjectMetaArgs:
    """
    Creates an ObjectMetaArgs with global labels and annotations.

    Args:
        name (str): The resource name.
        labels (Optional[Dict[str, str]]): Additional labels to apply.
        annotations (Optional[Dict[str, str]]): Additional annotations to apply.
        namespace (Optional[str]): Namespace for the resource.

    Returns:
        k8s.meta.v1.ObjectMetaArgs: The metadata arguments.
    """
    if labels is None:
        labels = {}
    if annotations is None:
        annotations = {}

    global_labels = get_global_labels()
    global_annotations = get_global_annotations()
    labels.update(global_labels)
    annotations.update(global_annotations)

    return k8s.meta.v1.ObjectMetaArgs(
        name=name,
        labels=labels,
        annotations=annotations,
        namespace=namespace,
        **kwargs,
    )
