import pulumi
import pulumi_kubernetes as k8s

def deploy_local_path_storage(k8s_provider: k8s.Provider, namespace: str, default_path: str):
    # Rancher local-path-provisioner URL
    url_local_path_provisioner = "https://github.com/rancher/local-path-provisioner/raw/master/deploy/local-path-storage.yaml"

    # Define a transformation function to modify the ConfigMap's config.json
    def configmap_transformation(obj):
        if obj["kind"] == "ConfigMap" and obj["metadata"]["name"] == "local-path-config":
            # Using an f-string to dynamically insert the value of default_path
            obj["data"]["config.json"] = f"""{{
                "nodePathMap":[{{
                    "node":"DEFAULT_PATH_FOR_NON_LISTED_NODES",
                    "paths":[
                        "{default_path}"
                    ]
                }}]
            }}"""
        return obj

    # Define a transformation function to modify the StorageClass and add the default class annotation
    def storageclass_transformation(obj):
        if obj["kind"] == "StorageClass" and obj["metadata"]["name"] == "local-path":
            # Update the volumeBindingMode
            obj["volumeBindingMode"] = "Immediate"
            # Add the annotation to make this the default storage class
            if "annotations" not in obj["metadata"]:
                obj["metadata"]["annotations"] = {}
            obj["metadata"]["annotations"]["storageclass.kubernetes.io/is-default-class"] = "true"
        return obj

    # Deploy local-path-provisioner using YAML configuration
    rancher_local_path_provisioner = k8s.yaml.ConfigFile(
        "rancherLocalPathProvisioner",
        file=url_local_path_provisioner,
        transformations=[
            configmap_transformation,
            storageclass_transformation
        ],
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    # Export the storage class name
    pulumi.export("modified_config_map_namespace", namespace)

    return(rancher_local_path_provisioner)
