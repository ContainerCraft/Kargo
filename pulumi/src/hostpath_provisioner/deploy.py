import requests
import pulumi
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s
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
        tag_url = 'https://github.com/kubevirt/hostpath-provisioner-operator/releases/latest'
        tag = requests.get(tag_url, allow_redirects=False).headers.get('location')
        version = tag.split('/')[-1] if tag else '0.17.0'

    # Create namespace
    ns_retain = True
    ns_protect = False
    ns_annotations = {}
    ns_labels = {
        "kubevirt.io": "",
        "kubernetes.io/metadata.name": ns_name,
    }
    namespace = create_namespace(
        depends,
        ns_name,
        ns_retain,
        ns_protect,
        k8s_provider,
        custom_labels=ns_labels,
        custom_annotations=ns_annotations
    )

    # Function to add namespace to resource if not set
    def add_namespace(args):
        obj = args.props

        if 'metadata' in obj:
            if isinstance(obj['metadata'], ObjectMetaArgs):
                if not obj['metadata'].namespace:
                    obj['metadata'].namespace = ns_name
            else:
                if not obj['metadata'].get('namespace'):
                    obj['metadata']['namespace'] = ns_name
        else:
            obj['metadata'] = {'namespace': ns_name}

        # Return the modified object wrapped in ResourceTransformationResult
        return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)

    # Deploy the webhook
    url_webhook = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/webhook.yaml'
    webhook = k8s.yaml.ConfigFile(
        "hostpath-provisioner-webhook",
        file=url_webhook,
        opts=ResourceOptions(
            provider=k8s_provider,
            transformations=[add_namespace],
            parent=namespace,
            depends_on=depends
        )
    )

    # Deploy the operator with a transformation that adds the namespace
    url_operator = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/v{version}/operator.yaml'
    operator = k8s.yaml.ConfigFile(
        "hostpath-provisioner-operator",
        file=url_operator,
        opts=ResourceOptions(
            provider=k8s_provider,
            transformations=[add_namespace],
            parent=namespace,
            depends_on=[webhook]
        )
    )

    # Create a HostPathProvisioner resource
    hostpath_provisioner = k8s.apiextensions.CustomResource(
        "hostpath-provisioner-hpp",
        api_version="hostpathprovisioner.kubevirt.io/v1beta1",
        kind="HostPathProvisioner",
        metadata={
            "name": "hostpath-provisioner-class-ssd",
            "namespace": ns_name
        },
        spec={
            "imagePullPolicy": "IfNotPresent",
            "storagePools": [{
                "name": "ssd",
                "path": hostpath
            }],
            "workload": {
                "nodeSelector": {
                    "kubernetes.io/os": "linux"
                }
            }
        },
        opts=ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=[namespace, operator, webhook]
        )
    )

    # Define the StorageClass
    storage_class = StorageClass(
        "hostpath-storage-class-ssd",
        metadata=ObjectMetaArgs(
            name="ssd",
            annotations={
                "storageclass.kubernetes.io/is-default-class": "true" if default else "false"
            }
        ),
        reclaim_policy="Delete",
        provisioner="kubevirt.io.hostpath-provisioner",
        volume_binding_mode="WaitForFirstConsumer",
        parameters={
            "storagePool": "ssd",
        },
        opts=ResourceOptions(
            provider=k8s_provider,
            parent=namespace,
            depends_on=[namespace, operator, webhook, hostpath_provisioner]
        )
    )

    return version, operator
