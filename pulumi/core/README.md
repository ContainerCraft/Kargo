# Core Module Developer Guide

Welcome to the **Core Module** of the Kargo KubeVirt Kubernetes PaaS project! This guide is designed to help both newcomers to DevOps and experienced module developers navigate and contribute to the core functionalities of the Kargo platform. Whether you're looking to understand the basics or dive deep into the module development, this guide has got you covered.

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Core Module Overview](#core-module-overview)
  - [Module Structure](#module-structure)
  - [Key Components](#key-components)
- [Detailed Explanation of Core Files](#detailed-explanation-of-core-files)
  - [config.py](#configpy)
  - [deployment.py](#deploymentpy)
  - [metadata.py](#metadatapy)
  - [resource_helpers.py](#resource_helperspy)
  - [types.py](#typespy)
  - [utils.py](#utilspy)
- [Best Practices](#best-practices)
- [Troubleshooting and FAQs](#troubleshooting-and-faqs)
- [Contributing to the Core Module](#contributing-to-the-core-module)
- [Additional Resources](#additional-resources)

---

## Introduction

The Core Module is the heart of the Kargo KubeVirt Kubernetes PaaS project. It provides essential functionalities that facilitate the development, deployment, and management of modules within the Kargo ecosystem. This guide aims to make core concepts accessible to everyone, regardless of their experience level in DevOps.

---

## Getting Started

If you're new to Kargo or DevOps, start here!

- **Prerequisites**:
  - Basic understanding of Python and Kubernetes.
  - [Pulumi CLI](https://www.pulumi.com/docs/get-started/) installed.
  - Access to a Kubernetes cluster (minikube, kind, or cloud-based).

- **Setup Steps**:
  1. **Clone the Repository**:
     ```bash
     git clone https://github.com/ContainerCraft/Kargo.git
     cd Kargo/pulumi
     ```
  2. **Install Dependencies**:
     ```bash
     pip install -r requirements.txt
     ```
  3. **Configure Pulumi**:
     ```bash
     pulumi login
     pulumi stack init dev
     ```

---

## Core Module Overview

### Module Structure

The Core Module is organized as follows:

```
pulumi/core/
├── __init__.py
├── README.md
├── config.py
├── deployment.py
├── metadata.py
├── resource_helpers.py
├── types.py
└── utils.py
```

### Key Components

- **Configuration Management**: Handles loading and merging of user configurations.
- **Deployment Orchestration**: Manages the deployment of modules and resources.
- **Metadata Management**: Generates and applies global labels and annotations.
- **Utility Functions**: Provides helper functions for common tasks.
- **Type Definitions**: Contains shared data structures used across modules.

---

## Detailed Explanation of Core Files

### config.py

**Purpose**: Manages configuration settings for modules, including loading defaults and exporting deployment results.

**Key Functions**:

- `get_module_config(module_name, config, default_versions)`: Retrieves and merges the configuration for a specific module.
- `load_default_versions(config, force_refresh=False)`: Loads default module versions, prioritizing user-specified sources.
- `export_results(versions, configurations, compliance)`: Exports deployment outputs for reporting and auditing.

**Usage Example**:

```python
from core.config import get_module_config

module_config, is_enabled = get_module_config('cert_manager', config, default_versions)
if is_enabled:
    # Proceed with deployment
```

---

### deployment.py

**Purpose**: Orchestrates the deployment of modules, initializing providers and handling dependencies.

**Key Functions**:

- `initialize_pulumi()`: Sets up Pulumi configurations and Kubernetes provider.
- `deploy_module(module_name, config, ...)`: Deploys a specified module, handling its configuration and dependencies.

**Usage Example**:

```python
from core.deployment import initialize_pulumi, deploy_module

init = initialize_pulumi()
deploy_module('kubevirt', init['config'], ...)
```

---

### metadata.py

**Purpose**: Manages global metadata, such as labels and annotations, ensuring consistency across resources.

**Key Components**:

- **Singleton Pattern**: Ensures a single source of truth for metadata.
- **Metadata Functions**:
  - `set_global_labels(labels)`
  - `set_global_annotations(annotations)`
  - `get_global_labels()`
  - `get_global_annotations()`

**Usage Example**:

```python
from core.metadata import set_global_labels

set_global_labels({'app': 'kargo', 'env': 'production'})
```

---

### resource_helpers.py

**Purpose**: Provides helper functions for creating Kubernetes resources with consistent metadata.

**Key Functions**:

- `create_namespace(name, labels, annotations, ...)`
- `create_custom_resource(name, args, ...)`
- `create_helm_release(name, args, ...)`

**Usage Example**:

```python
from core.resource_helpers import create_namespace

namespace = create_namespace('kargo-system', labels={'app': 'kargo'})
```

---

### types.py

**Purpose**: Defines shared data structures and configurations used across modules.

**Key Data Classes**:

- `NamespaceConfig`
- `FismaConfig`
- `NistConfig`
- `ScipConfig`
- `ComplianceConfig`

**Usage Example**:

```python
from core.types import ComplianceConfig

compliance_settings = ComplianceConfig(fisma=FismaConfig(enabled=True))
```

---

### utils.py

**Purpose**: Contains utility functions for common tasks such as version checking and resource transformations.

**Key Functions**:

- `set_resource_metadata(metadata, global_labels, global_annotations)`
- `get_latest_helm_chart_version(url, chart_name)`
- `is_stable_version(version_str)`

**Usage Example**:

```python
from core.utils import get_latest_helm_chart_version

latest_version = get_latest_helm_chart_version('https://charts.jetstack.io', 'cert-manager')
```

---

## Best Practices

- **Consistency**: Use the core functions and types to ensure consistency across modules.
- **Modularity**: Keep module-specific logic separate from core functionalities.
- **Documentation**: Document your code and configurations to aid future developers.
- **Error Handling**: Use appropriate error handling and logging for better debugging.

---

## Troubleshooting and FAQs

**Q1: I get a `ConnectionError` when deploying modules. What should I do?**

- **A**: Ensure your Kubernetes context is correctly configured and that you have network access to the cluster.

**Q2: How do I add a new module?**

- **A**: Create a new directory under `pulumi/modules/`, define your `deploy.py` and `types.py`, and update the main deployment script.

**Q3: The deployment hangs during resource creation.**

- **A**: Check for resource conflicts or namespace issues. Use `kubectl` to inspect the current state.

---

## Contributing to the Core Module

We welcome contributions from the community!

- **Reporting Issues**: Use the GitHub issues page to report bugs or request features.
- **Submitting Pull Requests**: Follow the project's coding standards and ensure all tests pass.
- **Code Reviews**: Participate in reviews to maintain high code quality.

---

## Additional Resources

- **Kargo Project Documentation**: [Kargo GitHub Repository](https://github.com/ContainerCraft/Kargo)
- **Pulumi Documentation**: [Pulumi Official Docs](https://www.pulumi.com/docs/)
- **Kubernetes API Reference**: [Kubernetes API](https://kubernetes.io/docs/reference/generated/kubernetes-api/)
