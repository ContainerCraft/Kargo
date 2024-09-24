# Kargo Modules Development Guide

Welcome to the Kargo Kubevirt PaaS IaC module developer guide. This document provides an overview of the design principles, code structure, and best practices for developing and maintaining modules within the Kargo IaC codebase. It is intended for developers and AI language models (like ChatGPT) to quickly understand and contribute to the project.

## Table of Contents

- [Introduction](#introduction)
- [Design Principles](#design-principles)
- [Code Structure](#code-structure)
- [Version Management](#version-management)
- [Module Development Guide](#module-development-guide)
  - [1. Module Configuration](#1-module-configuration)
  - [2. Defining Configuration Types](#2-defining-configuration-types)
  - [3. Module Deployment Logic](#3-module-deployment-logic)
  - [4. Updating `__main__.py`](#4-updating-__main__py)
- [Best Practices](#best-practices)
- [Example Module: Cert Manager](#example-module-cert-manager)
- [Conclusion](#conclusion)

---

## Introduction

Kargo is a Kubernetes & Kubevirt based Platform Engineering IaC development & deployment framework that leverages Pulumi for infrastructure as code (IaC). This guide aims to standardize module development by centralizing version handling, simplifying module code, and promoting consistency across the codebase.

---

## Design Principles

- **Centralization of Common Logic**: Shared functionality, such as version handling, is centralized to reduce duplication and simplify maintenance.
- **Simplification of Module Code**: Modules focus solely on their specific deployment logic, relying on centralized utilities for configuration and version management.
- **Consistency**: Establish clear patterns and standards for module development to ensure uniformity across the codebase.
- **Maintainability**: Write clean, readable code with proper documentation and type annotations to facilitate ease of maintenance and contribution.
- **Flexibility**: Allow users to override configurations and versions as needed, while providing sensible defaults.

---

## IaC Module Structure

- **`__main__.py`**: The entry point of the Pulumi program. Handles global configurations, Kubernetes provider setup, version loading, and module deployments.
- **`src/lib/`**: Contains shared utilities and libraries, such as version management (`versions.py`) and shared types (`types.py`).
- **`src/<module_name>/`**: Each module resides in its own directory under `src/`, containing its specific types (`types.py`) and deployment logic (`deploy.py`).
- **`src/<module_name>/types.py`**: Defines data classes for module configurations with default values and merging logic.
- **`src/<module_name>/deploy.py`**: Contains the module-specific deployment logic, taking in the merged configuration and returning relevant outputs.
- **`src/<module_name>/README.md`**: Module-specific documentation with configuration options, features, and usage instructions.
- **`src/<module_name>/*.py`**: Additional utility files or scripts specific to the module.

---

## Version Management

### Centralized Version Handling

Version management is centralized in `src/lib/versions.py`. The `load_default_versions` function loads versions based on the following precedence:

1. **User-Specified Source**: Via Pulumi config `default_versions.source`.
2. **Stack-Specific Versions**: If `versions.stack_name` is `true`, loads from `./versions/$STACK_NAME.json`.
3. **Local Default Versions**: Loads from `./default_versions.json`.
4. **Remote Versions**: Fetches from a remote URL based on the specified `versions.channel`.

### Injecting Versions into Modules

In `__main__.py`, the `get_module_config` function handles module configuration loading and version injection. Modules receive configurations with versions already set, eliminating the need for individual modules to handle version logic.

---

## Module Development Guide

Follow these steps to develop or enhance a module in the Kargo codebase.

### 1. Module Configuration

- **Purpose**: Retrieve and prepare the module's configuration, including version information.
- **Implementation**: Use the `get_module_config` function in `__main__.py`.

```python
# __main__.py

config_module_dict, module_enabled = get_module_config('module_name', config, default_versions)
```

- **Parameters**:
  - `module_name`: The name of the module as defined in Pulumi config.
  - `config`: The global Pulumi config object.
  - `default_versions`: The dictionary containing default versions.

### 2. Defining Configuration Types

- **Purpose**: Define a data class for the module's configuration with default values.
- **Implementation**: Create a `types.py` in the module's directory.

```python
# src/module_name/types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
import pulumi

@dataclass
class ModuleNameConfig:
    version: Optional[str] = None  # Version will be injected
    # ... other configuration fields ...

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'ModuleNameConfig':
        default_config = ModuleNameConfig()
        merged_config = default_config.__dict__.copy()
        for key, value in user_config.items():
            if hasattr(default_config, key):
                merged_config[key] = value
            else:
                pulumi.log.warn(f"Unknown configuration key '{key}' in module_name config.")
        return ModuleNameConfig(**merged_config)
```

### 3. Module Deployment Logic

- **Purpose**: Implement the module's deployment logic using the merged configuration.
- **Implementation**: Create a `deploy.py` in the module's directory.

```python
# src/module_name/deploy.py

def deploy_module_name(
    config_module_name: ModuleNameConfig,
    global_depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
    # Module-specific deployment logic
    # Use config_module_name.version as needed
    # Return version and any relevant resources
```

### 4. Updating `__main__.py`

- **Purpose**: Integrate the module into the main Pulumi program.
- **Implementation**:

```python
# __main__.py

if module_enabled:
    from src.module_name.types import ModuleNameConfig
    config_module_name = ModuleNameConfig.merge(config_module_dict)

    from src.module_name.deploy import deploy_module_name

    module_version, module_resource = deploy_module_name(
        config_module_name=config_module_name,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Update versions and configurations dictionaries
    versions["module_name"] = module_version
    configurations["module_name"] = {
        "enabled": module_enabled,
    }
```

---

## Best Practices

- **Centralize Common Logic**: Use shared utilities from `src/lib/` to avoid duplication.
- **Type Annotations**: Use type hints throughout the code for better readability and tooling support.
- **Documentation**: Include docstrings and comments to explain complex logic.
- **Consistent Coding Style**: Follow the project's coding conventions for formatting and naming.
- **Error Handling**: Implement robust error handling and logging for easier debugging.
- **Avoid Global Variables**: Pass necessary objects as arguments to functions and methods.

---

## Example Module: Cert Manager

### Configuration

```python
# Configurable by either of:
# - Pulumi Stack Config `Pulumi.stack.yaml`
# - Pulumi CLI `--config` flag
# - example: pulumi config set --path cert_manager.enabled true
# - example: pulumi config set --path cert_manager.version "1.15.3"
# - example: pulumi config set --path cert_manager.version "latest"
config:
  cert_manager:
    enabled: true
    version: "1.15.3"
```

### Types Definition

```python
# src/cert_manager/types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
import pulumi

@dataclass
class CertManagerConfig:
    version: Optional[str] = None
    # ... other fields ...

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
        # Merging logic as shown above
```

### Deployment Logic

```python
# src/cert_manager/deploy.py

def deploy_cert_manager_module(
    config_cert_manager: CertManagerConfig,
    global_depends_on: List[pulumi.Resource],
    k8s_provider: k8s.Provider,
) -> Tuple[Optional[str], Optional[pulumi.Resource], Optional[str]]:
    # Deployment logic for Cert Manager
    # Return version, release resource, and any additional outputs
```

### Integration in `__main__.py`

```python
# __main__.py

config_cert_manager_dict, cert_manager_enabled = get_module_config('cert_manager', config, default_versions)

if cert_manager_enabled:
    from src.cert_manager.types import CertManagerConfig
    config_cert_manager = CertManagerConfig.merge(config_cert_manager_dict)

    from src.cert_manager.deploy import deploy_cert_manager_module

    cert_manager_version, cert_manager_release, cert_manager_selfsigned_cert = deploy_cert_manager_module(
        config_cert_manager=config_cert_manager,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    versions["cert_manager"] = cert_manager_version
    configurations["cert_manager"] = {
        "enabled": cert_manager_enabled,
    }

    pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)
```
