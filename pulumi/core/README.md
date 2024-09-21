# Core Module Development Guide

This document provides an in-depth guide for developers, contributors, triage maintainers, and project maintainers working with the `core` module in the Kargo KubeVirt Kubernetes PaaS project. It includes a thorough overview of available functions, types, classes, and other core infrastructure details essential for productive module development.

## Table of Contents

- [Introduction](#introduction)
- [Core Components](#core-components)
  - [Compliance](#compliance)
  - [Configuration](#configuration)
  - [Deployment](#deployment)
  - [Helm Chart Versions](#helm-chart-versions)
  - [Initialization](#initialization)
  - [Introspection](#introspection)
  - [Metadata](#metadata)
  - [Namespace Management](#namespace-management)
  - [Types](#types)
  - [Utilities](#utilities)
  - [Version Management](#version-management)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing Guidelines](#contributing-guidelines)
- [Additional Resources](#additional-resources)

## Introduction

The `core` module is the backbone of the Kargo KubeVirt Kubernetes PaaS project. It houses essential functions, types, classes, and globals that facilitate the development and deployment of modules. This guide aims to equip you with the necessary knowledge to extend or maintain the core functionality effectively.

## Core Components

The core module is a collection of utilities and infrastructure necessary for the consistent and efficient deployment of modules in the Kargo platform. Below, we detail the key components and their usage.

### Compliance

Located in `pulumi/core/compliance.py`, this section deals with generating compliance-related labels and annotations.

#### Functions

- **`generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]`**
  Generates compliance labels.
- **`generate_compliance_annotations(compliance_config: ComplianceConfig) -> Dict[str, str]`**
  Generates compliance annotations.

#### Key Types

- **`ComplianceConfig`**
  Central configuration object for compliance settings.
- **`FismaConfig`, `NistConfig`, and `ScipConfig`**
  Nested configuration types used within `ComplianceConfig`.

### Configuration

Located in `pulumi/core/config.py`, this section handles module configuration parsing and loading.

#### Functions

- **`get_module_config(module_name: str, config: pulumi.Config, default_versions: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]`**
  Retrieves and prepares the configuration for a module.
- **`export_results(versions: Dict[str, str], configurations: Dict[str, Dict[str, Any]], compliance: Dict[str, Any])`**
  Exports deployment results including versions, configurations, and compliance information.

### Deployment

Located in `pulumi/core/deploy_module.py`, this section assists in deploying individual modules based on configuration.

#### Functions

- **`deploy_module(module_name: str, config: pulumi.Config, default_versions: Dict[str, Any], global_depends_on: List[pulumi.Resource], k8s_provider: k8s.Provider, versions: Dict[str, str], configurations: Dict[str, Dict[str, Any]]) -> None`**
  Helper function to deploy a module based on configuration.

### Helm Chart Versions

Located in `pulumi/core/helm_chart_versions.py`, this section provides functionality to manage Helm chart versions.

#### Functions

- **`is_stable_version(version_str: str) -> bool`**
  Determines if a version string represents a stable version.
- **`get_latest_helm_chart_version(url: str, chart_name: str) -> str`**
  Fetches the latest stable version of a Helm chart from a given URL.

### Initialization

Located in `pulumi/core/init.py`, this section initializes Pulumi configuration, Kubernetes provider, and global resources.

#### Functions

- **`initialize_pulumi() -> Dict[str, Any]`**
  Initializes Pulumi configuration, Kubernetes provider, and global resources.

### Introspection

Located in `pulumi/core/introspection.py`, this section provides functionality for discovering configuration classes and deploy functions.

#### Functions

- **`discover_config_class(module_name: str) -> Type`**
  Discovers and returns the configuration class from a module's `types.py`.
- **`discover_deploy_function(module_name: str) -> Callable`**
  Discovers and returns the deploy function from a module's `deploy.py`.

### Metadata

Located in `pulumi/core/metadata.py`, this section manages global metadata such as labels and annotations.

#### Functions

- **`set_global_labels(labels: Dict[str, str])`**
  Sets global labels.
- **`set_global_annotations(annotations: Dict[str, str])`**
  Sets global annotations.
- **`get_global_labels() -> Dict[str, str]`**
  Retrieves global labels.
- **`get_global_annotations() -> Dict[str, str]`**
  Retrieves global annotations.
- **`collect_git_info() -> Dict[str, str]`**
  Collects Git repository information.
- **`generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]`**
  Generates git-related labels.
- **`generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]`**
  Generates git-related annotations.

### Namespace Management

Located in `pulumi/core/namespace.py`, this section handles the creation and management of Kubernetes namespaces.

#### Functions

- **`create_namespace(config: NamespaceConfig, k8s_provider: k8s.Provider, depends_on: Optional[List[pulumi.Resource]] = None) -> k8s.core.v1.Namespace`**
  Creates a Kubernetes namespace with the provided configuration.

### Types

Located in `pulumi/core/types.py`, this section defines shared configuration types that are utilized by various modules.

#### Key Types

- **`NamespaceConfig`**
  Configuration object for Kubernetes namespaces.
- **`ComplianceConfig`, `FismaConfig`, `NistConfig`, and `ScipConfig`**
  Configuration objects for compliance settings.

### Utilities

Located in `pulumi/core/utils.py`, this section provides various utility functions for sanitizing labels, handling metadata, and more.

#### Functions

- **`set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str])`**
  Sets metadata for a given resource.
- **`generate_global_transformations(global_labels: Dict[str, str], global_annotations: Dict[str, str])`**
  Generates global transformations for resources.
- **`sanitize_label_value(value: str) -> str`**
  Sanitizes a label value to ensure compliance with Kubernetes naming conventions.
- **`extract_repo_name(remote_url: str) -> str`**
  Extracts the repository name from a Git remote URL.

### Version Management

Located in `pulumi/core/versions.py`, this section loads default versions for modules based on specified configuration settings.

#### Functions

- **`load_default_versions(config: pulumi.Config, force_refresh=False) -> dict`**
  Loads the default versions for modules based on configuration settings.

## Best Practices

- **Consistent Naming**: Follow consistent naming conventions for functions and variables.
- **Documentation**: Use detailed docstrings and comments to document your code.
- **Type Annotations**: Use type annotations to ensure readability and type safety.
- **Reusable Code**: Centralize reusable code in the `core` module to ensure consistency across modules.
- **Version Control**: Manage component versions to maintain consistency and avoid conflicts.

## Troubleshooting

- **Error Logging**: Use Pulumi's logging functions (`pulumi.log.info`, `pulumi.log.warn`, `pulumi.log.error`) to provide meaningful error messages.
- **Configuration Issues**: Ensure all configuration options are correctly set and validate input using type checks.
- **Module Dependencies**: Verify dependencies between modules are correctly resolved using Pulumi's dependency management features.

## Contributing Guidelines

- **Submit Issues**: Report bugs or request features via GitHub issues.
- **Pull Requests**: Submit pull requests with detailed descriptions and follow the project's coding standards.
- **Code Reviews**: Participate in code reviews to maintain code quality.

## Additional Resources

- **Kargo KubeVirt Documentation**: [GitHub Repository](https://github.com/containercraft/kargo)
- **Pulumi Documentation**: [Pulumi Documentation](https://www.pulumi.com/docs/)
