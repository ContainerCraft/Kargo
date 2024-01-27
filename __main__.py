import pulumi
import pulumi_kubernetes as kubernetes
import os

# Initialize Pulumi configuration
kubeconfig = os.getenv("KUBECONFIG")
config = pulumi.Config()

# Try to get the 'kargo:kubernetes.distribution' config value
kubernetes_distribution = config.get('kubernetes')

# Log the detected configuration
pulumi.log.info(f"Detected Configuration: kubernetes = {kubernetes_distribution}")

# Define a default value for kubeconfig_context
kubeconfig_context = "default-context"

# Determine the appropriate Kubernetes context based on the distribution type
if kubernetes_distribution == 'kind':
    kubeconfig_context = "kind-cilium"
elif kubernetes_distribution == 'talos':
    kubeconfig_context = "admin@talos-default"

# Initialize the Kubernetes provider with the chosen context
k8s_provider = kubernetes.Provider(
    "k8sProvider",
    context=kubeconfig_context,
    kubeconfig=pulumi.Output.secret(kubeconfig),
    suppress_deprecation_warnings=True,
    suppress_helm_hook_warnings=True,
    enable_server_side_apply=True
)

# Export the Kubernetes distribution and context
pulumi.export('kubernetes_distribution', kubernetes_distribution)
pulumi.export('kubeconfig_context', kubeconfig_context)
pulumi.export('k8s_provider', k8s_provider)