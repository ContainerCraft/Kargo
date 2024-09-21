# ./pulumi/core/introspection.py
# Description:

import inspect
import importlib
from typing import Type, Callable, Optional

def discover_config_class(module_name: str) -> Type:
    """
    Discovers and returns the configuration class from the module's types.py.

    Args:
        module_name (str): The name of the module.

    Returns:
        Type: The configuration class.
    """
    types_module = importlib.import_module(f"modules.{module_name}.types")
    for name, obj in inspect.getmembers(types_module):
        if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
            return obj
    raise ValueError(f"No dataclass found in modules.{module_name}.types")

def discover_deploy_function(module_name: str) -> Callable:
    """
    Discovers and returns the deploy function from the module's deploy.py.

    Args:
        module_name (str): The name of the module.

    Returns:
        Callable: The deploy function.
    """
    deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
    function_name = f"deploy_{module_name}_module"
    deploy_function = getattr(deploy_module, function_name, None)
    if not deploy_function:
        raise ValueError(f"No deploy function named '{function_name}' found in modules.{module_name}.deploy")
    return deploy_function
