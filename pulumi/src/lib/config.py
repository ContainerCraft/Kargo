# src/lib/config.py
# Description: Module Configuration Parsing & Loading

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
    default_versions: Dict[str, Any],
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
    # Get the module's configuration from Pulumi config, default to an empty dict
    module_config = config.get_object(module_name) or {}
    module_enabled = str(module_config.get('enabled', 'false')).lower() == "true"

    # Remove 'enabled' key from the module configuration
    module_config.pop('enabled', None)

    # Handle version injection into the module configuration
    module_version = module_config.get('version')
    if not module_version:
        # No version specified in module config; use default version
        module_version = default_versions.get(module_name)
        module_config['version'] = module_version

    return module_config, module_enabled

def export_results(versions: Dict[str, str], configurations: Dict[str, Dict[str, Any]], compliance: Dict[str, Any]):
    pulumi.export("versions", versions)
    pulumi.export("configuration", configurations)
    pulumi.export("compliance", compliance)
