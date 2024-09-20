# __main__.py
import pulumi
from src.lib.init import initialize_pulumi
from src.lib.config import export_results
from src.lib.deploy_module import deploy_module

# Pulumi Initialization
init = initialize_pulumi()

# Retrieve initialized resources
config = init["config"]
k8s_provider = init["k8s_provider"]
versions = init["versions"]
configurations = init["configurations"]
default_versions = init["default_versions"]
global_depends_on = init["global_depends_on"]
compliance_config = init["compliance_config"]

# List of modules to deploy
modules_to_deploy = ["cert_manager", "kubevirt"]

# Deploy each module
for module_name in modules_to_deploy:
    deploy_module(
        module_name=module_name,
        config=config,
        default_versions=default_versions,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
        versions=versions,
        configurations=configurations,
    )

# Export Component Metadata Outputs: - Versions - Configurations
export_results(versions, configurations, compliance_config)
