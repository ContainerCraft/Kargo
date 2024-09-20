# src/lib/deploy_module.py

import inspect
import pulumi
from typing import Any, Dict, List
from src.lib.introspection import discover_config_class, discover_deploy_function
from src.lib.config import get_module_config

def deploy_module(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: Any,
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]]
) -> None:
    """
    Helper function to deploy a module based on configuration.

    Args:
        module_name (str): Name of the module.
        config: Pulumi configuration object.
        default_versions: Default versions for modules.
        global_depends_on: Global dependencies.
        k8s_provider: Kubernetes provider.
        versions: Dictionary to store versions of deployed modules.
        configurations: Dictionary to store configurations of deployed modules.
    """
    # Get the module's configuration from Pulumi config
    module_config_dict, module_enabled = get_module_config(module_name, config, default_versions)

    if module_enabled:
        # Discover the configuration class and deploy function dynamically
        ModuleConfigClass = discover_config_class(module_name)
        deploy_func = discover_deploy_function(module_name)

        config_obj = ModuleConfigClass.merge(module_config_dict)

        # Infer the required argument name for the deploy function
        deploy_func_args = inspect.signature(deploy_func).parameters.keys()
        config_arg_name = list(deploy_func_args)[0]  # Assuming the first argument is the config object

        # Deploy the module using its deploy function with the correct arguments
        result = deploy_func(
            **{config_arg_name: config_obj},
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
        )

        # Handle the result based on its structure
        if isinstance(result, tuple) and len(result) == 3:
            version, release, exported_value = result
        elif isinstance(result, tuple) and len(result) == 2:
            version, release = result
            exported_value = None
        else:
            raise ValueError(f"Unexpected return value structure from {module_name} deploy function")

        # Record the deployed version and configuration
        versions[module_name] = version
        configurations[module_name] = {"enabled": module_enabled}

        # Export any additional values if needed
        if exported_value:
            pulumi.export(f"{module_name}_exported_value", exported_value)

        # Add the release to global dependencies to maintain resource ordering
        global_depends_on.append(release)
