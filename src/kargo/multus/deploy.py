import pulumi
import pulumi_kubernetes as k8s

def deploy_multus(k8s_provider: k8s.Provider):
    # multus thick deployment manifest
    url_local_path_provisioner = "https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml"

    # Deploy multus from YAML manifest
    multus = k8s.yaml.ConfigFile(
        "multus",
        file=url_local_path_provisioner,
        transformations=[],
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )

    return multus
