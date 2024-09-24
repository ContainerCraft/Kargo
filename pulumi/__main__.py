# pulumi/__main__.py

from typing import List, Dict, Any

import pulumi
from pulumi_kubernetes import Provider

from core.deployment import initialize_pulumi, deploy_modules
from core.config import export_results

def main():
    try:
        init = initialize_pulumi()

        config = init["config"]
        k8s_provider = init["k8s_provider"]
        versions = init["versions"]
        configurations = init["configurations"]
        default_versions = init["default_versions"]
        global_depends_on = init["global_depends_on"]

        modules_to_deploy = [
            "cert_manager",
            "kubevirt",
            "multus",
            "hostpath_provisioner",
            "containerized_data_importer",
            "prometheus"
        ]

        deploy_modules(
            modules_to_deploy,
            config,
            default_versions,
            global_depends_on,
            k8s_provider,
            versions,
            configurations,
        )

        compliance_config = init.get("compliance_config", {})
        export_results(versions, configurations, compliance_config)

    except Exception as e:
        pulumi.log.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
