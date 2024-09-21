# ./pulumi/__main__.py
# Description:

from typing import List, Dict, Any

import pulumi
from pulumi_kubernetes import Provider

from core.init import initialize_pulumi
from core.config import export_results
from core.deploy_module import deploy_module


def main():
    try:
        init = initialize_pulumi()

        config = init["config"]
        k8s_provider = init["k8s_provider"]
        versions = init["versions"]
        configurations = init["configurations"]
        default_versions = init["default_versions"]
        global_depends_on = init["global_depends_on"]

        modules_to_deploy = ["cert_manager", "kubevirt"]

        deploy_modules(modules_to_deploy, config, default_versions, global_depends_on, k8s_provider, versions, configurations)

        compliance_config = init.get("compliance_config", {})
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
