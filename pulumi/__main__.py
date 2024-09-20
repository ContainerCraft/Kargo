# __main__.py

# Import General Purpose Libraries
from typing import List, Dict, Any

# Import Pulumi Libraries
import pulumi
from pulumi_kubernetes import Provider

# Import Local Libraries
from core.init import initialize_pulumi
from core.config import export_results
from core.deploy_module import deploy_module


def main():
    """
    Main entry point for the Kargo Kubevirt Pulumi IaC.
    Initializes the Pulumi program, configures resources, and deploys specified modules.
    """
    try:
        # Initialize Pulumi resources
        init = initialize_pulumi()

        # Retrieve initialized resources
        config = init["config"]
        k8s_provider = init["k8s_provider"]
        versions = init["versions"]
        configurations = init["configurations"]
        default_versions = init["default_versions"]
        global_depends_on = init["global_depends_on"]
        compliance_config = init["compliance_config"]

        # Define the list of modules to deploy
        modules_to_deploy = ["cert_manager", "kubevirt"]

        # Deploy each module
        deploy_modules(modules_to_deploy, config, default_versions, global_depends_on, k8s_provider, versions, configurations)

        # Export results
        export_results(versions, configurations, compliance_config)

    except Exception as e:
        pulumi.log.error(f"Deployment failed: {str(e)}")
        raise

def deploy_modules(
        modules: List[str],
        config: pulumi.Config,
        default_versions: Dict[str, Any],
        global_depends_on: List[pulumi.Resource],
        k8s_provider: Provider,
        versions: Dict[str, str],
        configurations: Dict[str, Dict[str, Any]]
    ) -> None:
    """
    Deploy the specified modules.

    Args:
        modules (list): List of module names to deploy.
        config (pulumi.Config): The Pulumi configuration object.
        default_versions (dict): Default versions for modules.
        global_depends_on (list): Global dependencies.
        k8s_provider (Provider): Kubernetes provider object.
        versions (dict): Dictionary to store versions of deployed modules.
        configurations (dict): Dictionary to store configurations of deployed modules.
    """
    for module_name in modules:
        pulumi.log.info(f"Deploying module: {module_name}")
        deploy_module(
            module_name=module_name,
            config=config,
            default_versions=default_versions,
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
            versions=versions,
            configurations=configurations,
        )

if __name__ == "__main__":
    main()
