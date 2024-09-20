# src/lib/introspection.py
import inspect
import importlib
from typing import Type

def discover_config_class(module_name: str) -> Type:
    """
    Discovers and returns the configuration class from the module's types.py.
    Args:
        module_name (str): The name of the module.
    Returns:
        Type: The configuration class.
    """
    types_module = importlib.import_module(f"src.{module_name}.types")

    # Inspect the module to find dataclasses
    for name, obj in inspect.getmembers(types_module):
        if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
            # Developers note: module config dataclass is the first dataclass in src/<module_name>/types.py
            # src/<module_name>/types.py is a mandatory file and the first dataclass must exist and be the config class.
            return obj
    raise ValueError(f"No dataclass found in src.{module_name}.types")

def discover_deploy_function(module_name: str) -> callable:
    """
    Discovers and returns the deploy function from the module's deploy.py.
    Args:
        module_name (str): The name of the module.
    Returns:
        callable: The deploy function.
    """
    deploy_module = importlib.import_module(f"src.{module_name}.deploy")

    # Look for a deploy function that matches the pattern deploy_<module_name>_module
    function_name = f"deploy_{module_name}_module"
    deploy_function = getattr(deploy_module, function_name, None)

    if not deploy_function:
        raise ValueError(f"No deploy function named '{function_name}' found in src.{module_name}.deploy")

    return deploy_function
