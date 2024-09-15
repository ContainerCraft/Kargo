# pulumi/src/lib/deploy_module.py

# TODO: Implement the `deploy_module` function in __main__.py
#       Proceed with objective after all modules have been implemented.

from typing import Any, Dict, List, Tuple
import pulumi

def deploy_module(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: Any,
    deploy_function: Any,
    export_name: str
) -> None:
    """
    Helper function to deploy a module based on configuration.

    Args:
        module_name (str): Name of the module.
        config (pulumi.Config): Pulumi configuration object.
        default_versions (Dict[str, Any]): Default versions for modules.
        global_depends_on (List[pulumi.Resource]): Global dependencies.
        k8s_provider (Any): Kubernetes provider.
        deploy_function (Callable): Function to deploy the module.
        export_name (str): Name of the export variable.
    """
    module_config_dict, module_enabled = get_module_config(module_name, config, default_versions)

    if module_enabled:
        # Dynamically import the module's types and deploy function
        module_types = __import__(f"src.{module_name}.types", fromlist=[''])
        ModuleConfigClass = getattr(module_types, f"{module_name.capitalize()}Config")
        config_obj = ModuleConfigClass.merge(module_config_dict)

        module_deploy = __import__(f"src.{module_name}.deploy", fromlist=[''])
        deploy_func = getattr(module_deploy, f"deploy_{module_name}_module")

        version, release, exported_value = deploy_func(
            config_obj=config_obj,
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
        )

        versions[module_name] = version
        configurations[module_name] = {
            "enabled": module_enabled,
        }

        pulumi.export(export_name, exported_value)

# # Example Implementation
# from src.lib.deploy_helper import deploy_module

# # Deploy Cert Manager
# deploy_module(
#     module_name='cert_manager',
#     config=config,
#     default_versions=default_versions,
#     global_depends_on=global_depends_on,
#     k8s_provider=k8s_provider,
#     deploy_function=deploy_cert_manager_module,
#     export_name='cert_manager_selfsigned_cert'
# )
#
# # Deploy Ceph
# deploy_module(
#     module_name='ceph',
#     config=config,
#     default_versions=default_versions,
#     global_depends_on=global_depends_on,
#     k8s_provider=k8s_provider,
#     deploy_function=deploy_ceph_module,
#     export_name='ceph_release'
# )
