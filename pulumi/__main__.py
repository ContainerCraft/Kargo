# pulumi/__main__.py

from pulumi import log
from core.config import export_results
from core.deployment import initialize_pulumi, deploy_modules

def main():
    try:
        # Initialize Pulumi
        init = initialize_pulumi()

        # Extract the components from the initialization dictionary.
        # TODO:
        # - Refactor this to use dataclasses.
        # - Relocate the dataclasses to a shared location.
        # - Relocate module specific initialization logic into the pulumi/core/deployment.py module.
        config = init["config"]
        k8s_provider = init["k8s_provider"]
        versions = init["versions"]
        configurations = init["configurations"]
        default_versions = init["default_versions"]
        global_depends_on = init["global_depends_on"]
        compliance_config = init.get("compliance_config", {})

        # Map of modules to deploy with default boolean value.
        # TODO:
        # - Refactor this as a map of module names and default enabled booleans.
        # - Map of module:enabled pairs will depricate the DEFAULT_ENABLED_CONFIG list in config.py.
        modules_to_deploy = [
            "cert_manager",
            "kubevirt",
            "multus",
            "hostpath_provisioner",
            "containerized_data_importer",
            "prometheus"
        ]

        # Deploy modules
        # TODO:
        # - Simplify deploy_modules signature after relocating the module:enabled map and init dictionary location.
        deploy_modules(
            modules_to_deploy,
            config,
            default_versions,
            global_depends_on,
            k8s_provider,
            versions,
            configurations,
        )

        # Export stack outputs.
        export_results(versions, configurations, compliance_config)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        raise

# Entry point for the Pulumi program.
# TODO:
# - Re-evaluate structure and best location for export_results function call.
if __name__ == "__main__":
    main()
