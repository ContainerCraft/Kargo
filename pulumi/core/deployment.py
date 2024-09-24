# pulumi/core/deployment.py

"""
Deployment Management Module

This module manages the deployment orchestration of modules,
initializes Pulumi and Kubernetes providers, and handles module deployments.
"""

import os
import inspect
import importlib
from typing import Dict, Any, List, Type, Callable

import pulumi
import pulumi_kubernetes as k8s
from pulumi import log
from pulumi_kubernetes import Provider

from .config import get_module_config, load_default_versions
from .metadata import (
    collect_git_info,
    generate_git_labels,
    generate_git_annotations,
    set_global_labels,
    set_global_annotations,
    generate_compliance_labels,
    generate_compliance_annotations
)
from .utils import generate_global_transformations
from .types import ComplianceConfig

# Function to perform all prerequisite configuration retrieval and variable initialization.
# TODO: Evaluate all code to further improve centralized configuration and variable init.
def initialize_pulumi() -> Dict[str, Any]:
    """
    Initializes Pulumi configuration, Kubernetes provider, and global resources.

    Returns:
        Dict[str, Any]: A dictionary containing initialized components.
    """
    config = pulumi.Config()
    stack_name = pulumi.get_stack()
    project_name = pulumi.get_project()

    try:
        # Load global default versions and initialize variables from configuration.
        # TODO:
        # - Refactor this to utilize a dataclass for type safety and better organization.
        default_versions = load_default_versions(config)
        versions: Dict[str, str] = {}

        # Initialize empty global configuration and dependency list variables.
        configurations: Dict[str, Dict[str, Any]] = {}
        global_depends_on: List[pulumi.Resource] = []

        # Initialize the Kubernetes provider.
        kubernetes_config = config.get_object("kubernetes") or {}
        kubernetes_context = kubernetes_config.get("context")

        # TODO: refactor to export kubeconfig as a secret for use by k8s_provider.
        kubeconfig = kubernetes_config.get("kubeconfig") or os.getenv('KUBECONFIG')

        # Initialize the Kubernetes provider.
        # TODO:
        # - Refactor to utilized kubeconfig from pulumi secret export object to reduce risk of loss or exposure.
        k8s_provider = Provider(
            "k8sProvider",
            kubeconfig=kubeconfig,
            context=kubernetes_context,
        )

        # Export k8s_provider as secret for use in other pulumi stacks.
        k8s_provider_secret = pulumi.Output.secret(k8s_provider)
        pulumi.export("k8s_provider", k8s_provider_secret)

        log.info(f"Kubeconfig: {kubeconfig}")
        log.info(f"Kubernetes context: {kubernetes_context}")

        # Collect and store git information in the global configuration.
        # Global Compliance Metadata for global transformations to propagate as resource tag / label / annotations
        git_info = collect_git_info()
        configurations["source_repository"] = {
            "remote": git_info["remote"],
            "branch": git_info["branch"],
            "commit": git_info["commit"]
        }

        # Retrieve compliance metadata from pulumi configuration and generate global tags, labels, and annotations.
        # TODO:
        # - Evaluate for provider-specific structure and transformation to support Kubernetes, AWS, Azure, GCP, OpenStack, etc.
        compliance_config_dict = config.get_object('compliance') or {}
        compliance_config = ComplianceConfig.merge(compliance_config_dict)
        compliance_labels = generate_compliance_labels(compliance_config)
        compliance_annotations = generate_compliance_annotations(compliance_config)

        git_labels = generate_git_labels(git_info)
        git_annotations = generate_git_annotations(git_info)
        global_labels = {**compliance_labels, **git_labels}
        global_annotations = {**compliance_annotations, **git_annotations}

        set_global_labels(global_labels)
        set_global_annotations(global_annotations)
        generate_global_transformations(global_labels, global_annotations)

        # Return the initialized components.
        # TODO: Refactor this as a dataclas, namedtuple, or similar.
        return {
            "config": config,
            "stack_name": stack_name,
            "project_name": project_name,
            "default_versions": default_versions,
            "versions": versions,
            "configurations": configurations,
            "global_depends_on": global_depends_on,
            "k8s_provider": k8s_provider,
            "git_info": git_info,
            "compliance_config": compliance_config,
            "global_labels": global_labels,
            "global_annotations": global_annotations,
        }
    except Exception as e:
        log.error(f"Initialization error: {str(e)}")
        raise

# Reusable function to deploy any IaC module with dynamic configuration and versioning.
def deploy_module(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
    versions: Dict[str, str],
    configurations: Dict[str, Dict[str, Any]]
) -> None:
    """
    Helper function to deploy a module based on configuration.

    Args:
        module_name (str): Name of the module.
        config (pulumi.Config): Pulumi configuration object.
        default_versions (Dict[str, Any]): Default versions for modules.
        global_depends_on (List[pulumi.Resource]): Global dependencies.
        k8s_provider (k8s.Provider): Kubernetes provider.
        versions (Dict[str, str]): Dictionary to store versions of deployed modules.
        configurations (Dict[str, Dict[str, Any]]): Dictionary to store configurations of deployed modules.

    Raises:
        TypeError: If any arguments have incorrect types.
        ValueError: If any module-specific errors occur.
    """

    # Validate input types.
    # TODO: Evalute for better approach to type checking.
    if not isinstance(module_name, str):
        raise TypeError("module_name must be a string")
    if not isinstance(config, pulumi.Config):
        raise TypeError("config must be an instance of pulumi.Config")
    if not isinstance(default_versions, dict):
        raise TypeError("default_versions must be a dictionary")
    if not isinstance(global_depends_on, list):
        raise TypeError("global_depends_on must be a list")
    if not isinstance(k8s_provider, k8s.Provider):
        raise TypeError("k8s_provider must be an instance of pulumi_kubernetes.Provider")
    if not isinstance(versions, dict):
        raise TypeError("versions must be a dictionary")
    if not isinstance(configurations, dict):
        raise TypeError("configurations must be a dictionary")

    # Retrieve module configuration and enabled status.
    module_config_dict, module_enabled = get_module_config(module_name, config, default_versions)

    # Deploy the module if enabled.
    if module_enabled:

        # Discover module configuration class and deploy function.
        ModuleConfigClass = discover_config_class(module_name)
        deploy_func = discover_deploy_function(module_name)

        # Merge module's default and user supplied configuration values.
        config_obj = ModuleConfigClass.merge(module_config_dict)

        # Validate the configuration object.
        deploy_func_args = inspect.signature(deploy_func).parameters.keys()
        config_arg_name = list(deploy_func_args)[0]

        # Deploy the module.
        try:

            # Execute the module's deploy function.
            result = deploy_func(
                **{config_arg_name: config_obj},
                global_depends_on=global_depends_on,
                k8s_provider=k8s_provider,
            )

            # Parse the result for version and release information.
            # Accommodate for optional exported value.
            # TODO:
            # - Refactor this to be more robust and less restrictive.
            # - Refactor to inherit value names from name string of returned key arguments.
            if isinstance(result, tuple) and len(result) == 3:
                version, release, module_aux_meta = result
            elif isinstance(result, tuple) and len(result) == 2:
                version, release = result
                module_aux_meta = None
            else:
                raise ValueError(f"Unexpected return value structure from {module_name} deploy function")

            # Append the module's version and configuration to the global dictionaries.
            versions[module_name] = version
            configurations[module_name] = {"enabled": module_enabled}

            # adopt value export names from the returned key name argument string if possible, else solve for naming positional args.
            if module_aux_meta:
                pulumi.export(f"meta_{module_name}", module_aux_meta)

            # Append the module to the global dependencies.
            # TODO: Reevaluate optimization for global_depends_on and best location for appending each module's primary resource.'
            global_depends_on.append(release)

        except Exception as e:
            log.error(f"Deployment failed for module {module_name}: {str(e)}")
            raise

    # Report to log if module is not enabled.
    else:
        log.info(f"Module {module_name} is not enabled.")

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

# TODO:
# - Refactor to use a more robust approach to type checking.
# - Reevaluate deploy_module signature and optimize on existing argument encapsulation and passing for simpler module developer experience.
def deploy_modules(
        modules: List[str],
        config: pulumi.Config,
        default_versions: Dict[str, Any],
        global_depends_on: List[pulumi.Resource],
        k8s_provider: Provider,
        versions: Dict[str, str],
        configurations: Dict[str, Dict[str, Any]],
    ) -> None:

    for module_name in modules:
        log.info(f"Deploying module: {module_name}")
        deploy_module(
            module_name=module_name,
            config=config,
            default_versions=default_versions,
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
            versions=versions,
            configurations=configurations,
        )
