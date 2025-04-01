import pulumi
from pulumi_kubernetes import helm, Provider

import pulumi_kubernetes as k8s
from kubernetes import config, dynamic
from kubernetes import client as k8s_client
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from kubernetes.client import api_client



def deploy_ui_for_kubevirt(name: str, k8s_provider: Provider):
    # Initialize Pulumi configuration
    pconfig = pulumi.Config()

    # There's no helm chart for kubevirt-manager so <christopher walken shrug>
    kubevirt_manager_manifest_url = 'https://raw.githubusercontent.com/kubevirt-manager/kubevirt-manager/main/kubernetes/bundled.yaml'
    k8s_yaml = k8s.yaml.ConfigFile(
        "kubevirt-manager",
        file=kubevirt_manager_manifest_url,
        opts=pulumi.ResourceOptions(provider=k8s_provider)
    )
    return "1.4.1", k8s_yaml
