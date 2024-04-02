import pulumi
import pulumi_kubernetes as k8s
import requests

def deploy(k8s_provider: k8s.Provider, hostpath: str, default: str, version: str = None, cert_manager: pulumi.Output = None):
    # If version is not supplied, fetch the latest stable version
    if version is None:
        tag_url = 'https://github.com/kubevirt/hostpath-provisioner-operator/releases/latest'
        tag = requests.get(tag_url, allow_redirects=False).headers.get('location')
        version = tag.split('/')[-1] if tag else 'v0.17.0'

    # Deploy the namespace
    url = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/{version}/namespace.yaml'
    namespace = k8s.yaml.ConfigFile(
        'namespace',
        file=url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[cert_manager]
        )
    )

    # Function to add namespace to resource if not set
    def add_namespace(args):
        obj = args.props
        if 'metadata' in obj:
            if not obj['metadata'].get('namespace'):
                obj['metadata']['namespace'] = 'hostpath-provisioner'
        else:
            obj['metadata'] = {'namespace': 'hostpath-provisioner'}

        # Return the modified object wrapped in ResourceTransformationResult
        return pulumi.ResourceTransformationResult(props=obj, opts=args.opts)

    # Deploy the webhook
    url = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/{version}/webhook.yaml'
    webhook = k8s.yaml.ConfigFile(
        'webhook',
        file=url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            transformations=[add_namespace],
            depends_on=[namespace]
        )
    )

    # Deploy the operator with a transformation that adds the namespace
    url = f'https://github.com/kubevirt/hostpath-provisioner-operator/releases/download/{version}/operator.yaml'
    operator = k8s.yaml.ConfigFile(
        'operator',
        file=url,
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            transformations=[add_namespace],
            depends_on=[namespace]
        )
    )

    # Create a HostPathProvisioner resource
    hostpath_provisioner = k8s.apiextensions.CustomResource(
        "hostpath-provisioner",
        api_version="hostpathprovisioner.kubevirt.io/v1beta1",
        kind="HostPathProvisioner",
        metadata={
            "name": "hostpath-provisioner",
            "namespace": "hostpath-provisioner"
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
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[webhook]
        )
    )

    # Define the StorageClass
    storage_class = k8s.storage.v1.StorageClass(
        "storage_class_ssd",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ssd",
            namespace="hostpath-provisioner",
            annotations={
                "storageclass.kubernetes.io/is-default-class": default
            }
        ),
        reclaim_policy="Delete",
        provisioner="kubevirt.io.hostpath-provisioner",
        volume_binding_mode="WaitForFirstConsumer",
        parameters={
            "storagePool": "ssd",
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[namespace, operator, webhook, hostpath_provisioner]
        )
    )

    # To access the name of the provisioner once it is created, you can export the value:
    pulumi.export("provisioner_name", hostpath_provisioner.metadata["name"])

    # Export the name of the StorageClass
    pulumi.export("storage_class_name", storage_class.metadata["name"])

    # Export the version of the hostpath provisioner operator that was deployed
    pulumi.export("hostpath_provisioner_operator_version", version)

    return {
        "version": version,
        "namespace": namespace,
        "webhook": webhook,
        "operator": operator,
        "hostpath_provisioner": hostpath_provisioner,
        "storage_class": storage_class
    }
