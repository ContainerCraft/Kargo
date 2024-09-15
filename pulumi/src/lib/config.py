# pulumi/src/lib/config.py

"""
Configuration Management Module

This module handles the retrieval and preparation of configurations for different modules
within the Kargo Pulumi IaC program. It centralizes configuration logic to promote reuse
and maintainability.
"""

from typing import Any, Dict, Tuple
import pulumi

def get_module_config(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """
    Retrieves and prepares the configuration for a module.

    Args:
        module_name (str): The name of the module to configure.
        config (pulumi.Config): The Pulumi configuration object.
        default_versions (Dict[str, Any]): A dictionary of default versions for modules.

    Returns:
        Tuple[Dict[str, Any], bool]:

        A tuple containing the module's configuration dictionary
        and a boolean indicating if the module is enabled.
    """
    # Get the module's configuration from Pulumi config, default to {"enabled": "false"} if not set
    module_config = config.get_object(module_name) or {"enabled": "false"}
    module_enabled = str(module_config.get('enabled', 'false')).lower() == "true"

    # Remove 'enabled' key from the module configuration as modules do not need this key beyond this point
    module_config.pop('enabled', None)

    # Handle version injection into the module configuration
    module_version = module_config.get('version')
    if not module_version:
        # No version specified in module config; use default version
        module_version = default_versions.get(module_name)
        if module_version:
            module_config['version'] = module_version
        else:
            # No default version available; set to None (module will handle this case)
            module_config['version'] = None
    else:
        # Version is specified in module config; keep as is (could be 'latest' or a specific version)
        pass

    return module_config, module_enabled

def export_results(versions: Dict[str, str], configurations: Dict[str, Dict[str, Any]]):
    pulumi.export("versions", versions)
    pulumi.export("configuration", configurations)
