# Kargo Module Developmer Guide

This document provides an in-depth guide for developers, contributors, triage maintainers, and project maintainers utilizing the `core` module in the Kargo KubeVirt Kubernetes PaaS project. It includes a thorough overview of available functions, types, classes, and other core infrastructure details essential for productive module development.

## Table of Contents

- [Introduction](#introduction)
- [Core Module Structure](#core-module-structure)
  - [config.py](#configpy)
  - [deployment.py](#deploymentpy)
  - [metadata.py](#metadatapy)
  - [utils.py](#utilspy)
  - [types.py](#typespy)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing Guidelines](#contributing-guidelines)
- [Additional Resources](#additional-resources)

---

## Introduction

The `core` module is the backbone of the Kargo KubeVirt Kubernetes PaaS project. It houses essential functions, types, classes, and globals that facilitate the development and deployment of modules. This guide aims to equip you with the necessary knowledge to extend or maintain the core functionality effectively.

## Core Module Structure

The `core` module structure:

```
pulumi/core/
├── __init__.py
├── README.md
├── config.py
├── deployment.py
├── metadata.py
├── utils.py
└── types.py
```

### config.py

**Responsibilities:**

- Handle all configuration-related functionalities.
- Load and merge user configurations with defaults.
- Load default versions for modules.
- Export deployment results.

**Key Functions:**

- `get_module_config(module_name, config, default_versions)`: Retrieves and prepares the configuration for a module.
- `load_default_versions(config, force_refresh=False)`: Loads the default versions for modules based on the specified configuration settings.
- `export_results(versions, configurations, compliance)`: Exports the results of the deployment processes including versions, configurations, and compliance information.

**Key Types:**

- `ComplianceConfig`: Central configuration object for compliance settings (imported from `types.py`).

---

### deployment.py

**Responsibilities:**

- Manage the deployment orchestration of modules.
- Initialize Pulumi and Kubernetes providers.
- Deploy individual modules based on configuration.
- Discover module-specific configuration classes and deploy functions.

**Key Functions:**

- `initialize_pulumi()`: Initializes Pulumi configuration, Kubernetes provider, and global resources.
- `deploy_module(module_name, config, default_versions, global_depends_on, k8s_provider, versions, configurations)`: Helper function to deploy a module based on configuration.
- `discover_config_class(module_name)`: Discovers and returns the configuration class from the module's `types.py`.
- `discover_deploy_function(module_name)`: Discovers and returns the deploy function from the module's `deploy.py`.

---

### metadata.py

**Responsibilities:**

- Manage global metadata, labels, and annotations.
- Generate compliance and Git-related metadata.
- Sanitize label values to comply with Kubernetes naming conventions.

**Key Classes and Functions:**

- `MetadataSingleton`: Singleton class to store global labels and annotations.
- `set_global_labels(labels)`: Sets global labels.
- `set_global_annotations(annotations)`: Sets global annotations.
- `get_global_labels()`: Retrieves global labels.
- `get_global_annotations()`: Retrieves global annotations.
- `collect_git_info()`: Collects Git repository information.
- `generate_git_labels(git_info)`: Generates Git-related labels.
- `generate_git_annotations(git_info)`: Generates Git-related annotations.
- `generate_compliance_labels(compliance_config)`: Generates compliance labels.
- `generate_compliance_annotations(compliance_config)`: Generates compliance annotations.
- `sanitize_label_value(value)`: Sanitizes a label value to comply with Kubernetes naming conventions.

---

### utils.py

**Responsibilities:**

- Provide utility functions that are generic and reusable.
- Handle tasks like resource transformations and Helm interactions.
- Extract repository names from Git URLs.

**Key Functions:**

- `set_resource_metadata(metadata, global_labels, global_annotations)`: Updates resource metadata with global labels and annotations.
- `generate_global_transformations(global_labels, global_annotations)`: Generates global transformations for resources.
- `get_latest_helm_chart_version(url, chart_name)`: Fetches the latest stable version of a Helm chart from the given URL.
- `is_stable_version(version_str)`: Determines if a version string represents a stable version.
- `extract_repo_name(remote_url)`: Extracts the repository name from a Git remote URL.

---

### types.py

**Responsibilities:**

- Define all shared data classes and types used across modules.

**Key Data Classes:**

- `NamespaceConfig`: Configuration object for Kubernetes namespaces.
- `FismaConfig`: Configuration for FISMA compliance settings.
- `NistConfig`: Configuration for NIST compliance settings.
- `ScipConfig`: Configuration for SCIP compliance settings.
- `ComplianceConfig`: Central configuration object for compliance settings.

**Methods:**

- `ComplianceConfig.merge(user_config)`: Merges user-provided compliance configuration with default configuration.

---

## Best Practices

- **Consistent Naming**: Follow consistent naming conventions for functions and variables.
- **Documentation**: Use detailed docstrings and comments to document your code.
- **Type Annotations**: Use type annotations to enhance readability and type safety.
- **Reusable Code**: Centralize reusable code in the `core` module to ensure consistency across modules.
- **Version Control**: Manage component versions to maintain consistency and avoid conflicts.

---

## Troubleshooting

- **Error Logging**: Use Pulumi's logging functions (`pulumi.log.info`, `pulumi.log.warn`, `pulumi.log.error`) to provide meaningful error messages.
- **Configuration Issues**: Ensure all configuration options are correctly set and validate input using type checks.
- **Module Dependencies**: Verify dependencies between modules are correctly resolved using Pulumi's dependency management features.
- **Resource Conflicts**: Be cautious of naming collisions in Kubernetes resources; use namespaces and labels appropriately.

---

## Contributing Guidelines

- **Submit Issues**: Report bugs or request features via GitHub issues.
- **Pull Requests**: Submit pull requests with detailed descriptions and follow the project's coding standards.
- **Code Reviews**: Participate in code reviews to maintain code quality.
- **Testing**: Write unit tests for new functions and ensure existing tests pass.

---

## Additional Resources

- **Kargo KubeVirt Documentation**: [GitHub Repository](https://github.com/containercraft/kargo)
- **Pulumi Documentation**: [Pulumi Docs](https://www.pulumi.com/docs/)
- **Kubernetes API Reference**: [Kubernetes API](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.20/)
- **Python Dataclasses**: [Dataclasses Documentation](https://docs.python.org/3/library/dataclasses.html)
