# Kargo KubeVirt Kubernetes PaaS - Pulumi Python Infrastructure as Code (IaC)

Welcome to the **Kargo KubeVirt Kubernetes PaaS Pulumi Infrastructure as Code (IaC) project**! This guide is designed to help both newcomers to DevOps and experienced module developers navigate, contribute to, and get the most out of the Kargo platform. Whether you're setting up your environment for the first time or looking to develop new modules, this guide provides comprehensive instructions and best practices.

---

## Table of Contents

- [Introduction](#introduction)
- [Developer & Architecture Ethos](#developer--architecture-ethos)
  - [Prime Directive](#prime-directive)
  - [Developer Directives](#developer-directives)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setting Up Your Environment](#setting-up-your-environment)
- [Developer Imperatives](#developer-imperatives)
  - [Detailed Breakdown](#detailed-breakdown)
- [Developing New Modules](#developing-new-modules)
  - [Directory Structure](#directory-structure)
  - [Creating a New Module](#creating-a-new-module)
- [Common Utilities](#common-utilities)
- [Version Control](#version-control)
- [Contributing to the Project](#contributing-to-the-project)
- [Additional Resources](#additional-resources)
- [Conclusion](#conclusion)

---

## Introduction

The Kargo KubeVirt Kubernetes PaaS project leverages Pulumi and Python to manage your Kubernetes infrastructure as code. Our goal is to provide an enjoyable developer experience (DX) and user experience (UX) by simplifying the deployment and management of Kubernetes resources, including KubeVirt virtual machines and other essential components.

This guide aims to make core concepts accessible to everyone, regardless of their experience level in DevOps.

---

## Developer & Architecture Ethos

### Prime Directive

> **"Features are nice. Quality is paramount."**

Quality is not just about the product or code; it's about creating an enjoyable developer and user experience. At ContainerCraft, we believe that the success of open-source projects depends on the happiness and satisfaction of the community developers and users.

### Developer Directives

1. **Improve Code Maintainability**: Write code that is structured, organized, and easy to understand. Prioritize readability, reusability, and extensibility.

2. **Optimize Performance**: Ensure that the code performs efficiently and respects configurations. Avoid executing inactive or unnecessary code.

3. **Establish Standard Practices**: Develop consistent approaches to configuration handling, module deployment, and code organization to guide future development.

---

## Getting Started

### Prerequisites

Before you begin, make sure you have the following installed:

- **Pulumi CLI**: [Install Pulumi](https://www.pulumi.com/docs/get-started/)
- **Python 3.6+**: Ensure you have Python installed on your system.
- **Python Dependencies**: Install required Python packages using `pip install -r requirements.txt`
- **Kubernetes Cluster**: Access to a Kubernetes cluster with `kubectl` configured.
- **Helm CLI**: [Install Helm](https://helm.sh/docs/intro/install/) if you plan to work with Helm charts.

### Setting Up Your Environment

Follow these steps to set up your environment:

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ContainerCraft/Kargo.git
   cd Kargo/pulumi
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Pulumi Stack**

   ```bash
   pulumi stack init dev
   ```

4. **Configure Pulumi**

   Set your Kubernetes context and any necessary configuration options.

   ```bash
   pulumi config set kubernetes:kubeconfig <path-to-kubeconfig>
   # Set other configuration options as needed
   ```

5. **Deploy the Stack**

   Preview and deploy your changes.

   ```bash
   pulumi up
   ```

   Follow the prompts to confirm the deployment.

---

## Developer Imperatives

### Detailed Breakdown

1. **User Experience (UX)**

   - **Clear Error Messages**: Provide meaningful error messages to help users resolve issues.
   - **Uniform Logging**: Use consistent logging practices to make debugging easier.

     ```python
     pulumi.log.info(f"Deploying module: {module_name}")
     ```

2. **Developer Experience (DX)**

   - **Documentation**: Include comprehensive docstrings and comments in your code.

     ```python
     def deploy_module(...):
         """
         Deploys a module based on configuration.

         Args:
             module_name (str): Name of the module.
             config (pulumi.Config): Pulumi configuration object.
             ...

         Returns:
             None
         """
     ```

   - **Examples**: Provide example configurations and usage in the documentation to help others understand how to use your code.

3. **Configurable Modules**

   - **Pulumi Stack Configuration**: Use the Pulumi config object to allow users to customize module configurations.

     ```python
     module_config = config.get_object("module_name") or {}
     ```

4. **Module Data Classes**

   - **Typed Data Classes**: Use `dataclass` to encapsulate configurations clearly.

     ```python
     from dataclasses import dataclass

     @dataclass
     class KubeVirtConfig:
         namespace: str = "default"
     ```

5. **Sane Defaults in Data Classes**

   - **Sensible Defaults**: Set reasonable default values to minimize the need for user configuration.

     ```python
     @dataclass
     class CertManagerConfig:
         namespace: str = "cert-manager"
         install_crds: bool = True
     ```

6. **User Configuration Handling**

   - **Merge Configurations**: Combine user-provided configurations with defaults to ensure all necessary parameters are set.

     ```python
     @staticmethod
     def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
         default_config = CertManagerConfig()
         for key, value in user_config.items():
             if hasattr(default_config, key):
                 setattr(default_config, key, value)
             else:
                 pulumi.log.warn(f"Unknown configuration key '{key}' in cert_manager config.")
         return default_config
     ```

7. **Simple Function Signatures**

   - **Reduce Parameters**: Keep function signatures minimal by encapsulating configurations within data classes.

     ```python
     def deploy_module(config_module: ModuleConfig, ...)
     ```

8. **Type Annotations**

   - **Enhance Readability**: Use type annotations to clarify expected parameter types and return values.

     ```python
     def deploy_module(module_name: str, config: pulumi.Config) -> None:
     ```

9. **Safe Function Signatures**

   - **Type Safety**: Use consistent type checks and raise meaningful errors when types don't match expectations.

     ```python
     if not isinstance(module_name, str):
         raise TypeError("module_name must be a string")
     ```

10. **Streamlined Entrypoint**

    - **Encapsulate Logic**: Keep the top-level code minimal and encapsulate logic within functions.

      ```python
      if __name__ == "__main__":
          main()
      ```

11. **Reuse and Deduplicate Code**

    - **Central Utilities**: Place reusable code in the `core` module to maintain consistency and reduce duplication.

      ```python
      from core.utils import sanitize_label_value, extract_repo_name
      ```

12. **Version Control Dependencies**

    - **Manage Versions**: Control component versions within configuration files to maintain consistency across deployments.

      ```python
      default_versions = load_default_versions(config)
      ```

13. **Transparency**

    - **Informative Outputs**: Export configuration and version information for visibility and auditing.

      ```python
      pulumi.export("versions", versions)
      ```

14. **Conditional Execution**

    - **Avoid Unnecessary Execution**: Only load and execute modules that are enabled in the configuration.

      ```python
      if module_enabled:
          deploy_func(...)
      ```

15. **Remove Deprecated Code**

    - **Maintain a Clean Codebase**: Remove obsolete features and update code to align with current best practices.

---

## Developing New Modules

### Directory Structure

Maintain a consistent directory structure for new modules:

```
kargo/
  pulumi/
    __main__.py
    requirements.txt
    core/
      __init__.py
      utils.py
      ...
    modules/
      <new_module>/
        __init__.py
        deploy.py
        types.py
        README.md
        ...
```

### Creating a New Module

1. **Define Configuration**

   Create a `types.py` file in your module directory to define the configuration data class:

   ```python
   from dataclasses import dataclass, field
   from typing import Optional, Dict, Any

   @dataclass
   class NewModuleConfig:
       version: Optional[str] = None
       namespace: str = "default"
       labels: Dict[str, str] = field(default_factory=dict)
       annotations: Dict[str, Any] = field(default_factory=dict)

       @staticmethod
       def merge(user_config: Dict[str, Any]) -> 'NewModuleConfig':
           default_config = NewModuleConfig()
           for key, value in user_config.items():
               if hasattr(default_config, key):
                   setattr(default_config, key, value)
               else:
                   pulumi.log.warn(f"Unknown configuration key '{key}' in new_module config.")
           return default_config
   ```

2. **Implement Deployment Logic**

   Define the deployment logic in `deploy.py`:

   ```python
   import pulumi
   import pulumi_kubernetes as k8s
   from typing import List, Dict, Any, Tuple, Optional

   from core.metadata import get_global_labels, get_global_annotations
   from core.resource_helpers import create_namespace
   from .types import NewModuleConfig

   def deploy_new_module(
           config_new_module: NewModuleConfig,
           global_depends_on: List[pulumi.Resource],
           k8s_provider: k8s.Provider,
       ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
       # Create Namespace
       namespace_resource = create_namespace(
           name=config_new_module.namespace,
           labels=config_new_module.labels,
           annotations=config_new_module.annotations,
           k8s_provider=k8s_provider,
           depends_on=global_depends_on,
       )

       # Implement specific resource creation logic
       # ...

       return config_new_module.version, namespace_resource
   ```

3. **Update `__main__.py`**

   Include your module in the main deployment script:

   ```python
   from typing import List, Dict, Any
   import pulumi
   from pulumi_kubernetes import Provider

   from core.deployment import initialize_pulumi, deploy_module
   from core.config import export_results

   def main():
       try:
           init = initialize_pulumi()

           config = init["config"]
           k8s_provider = init["k8s_provider"]
           versions = init["versions"]
           configurations = init["configurations"]
           default_versions = init["default_versions"]
           global_depends_on = init["global_depends_on"]

           modules_to_deploy = ["cert_manager", "kubevirt", "new_module"]  # Add your module here

           deploy_modules(
               modules=modules_to_deploy,
               config=config,
               default_versions=default_versions,
               global_depends_on=global_depends_on,
               k8s_provider=k8s_provider,
               versions=versions,
               configurations=configurations,
           )

           compliance_config = init.get("compliance_config", {})
           export_results(versions, configurations, compliance_config)

       except Exception as e:
           pulumi.log.error(f"Deployment failed: {str(e)}")
           raise

   if __name__ == "__main__":
       main()
   ```

4. **Document Your Module**

   Create a `README.md` file in your module directory to document its purpose, configuration options, and usage instructions.

   ```markdown
   # New Module

   Description of your module.

   ## Configuration

   - **version** *(string)*: The version of the module to deploy.
   - **namespace** *(string)*: The Kubernetes namespace where the module will be deployed.
   - **labels** *(dict)*: Custom labels to apply to resources.
   - **annotations** *(dict)*: Custom annotations to apply to resources.

   ## Usage

   Example of how to configure and deploy the module.

   ## Additional Information

   Any additional details or resources.
   ```

---

## Common Utilities

Refer to `core/utils.py` for common helper functions, such as applying global labels and annotations to resources.

```python
import re
import pulumi
import pulumi_kubernetes as k8s
from typing import Dict, Any

def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    if isinstance(metadata, dict):
        metadata.setdefault('labels', {}).update(global_labels)
        metadata.setdefault('annotations', {}).update(global_annotations)
    elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
        metadata.labels = {**metadata.labels or {}, **global_labels}
        metadata.annotations = {**metadata.annotations or {}, **global_annotations}

def sanitize_label_value(value: str) -> str:
    value = value.lower()
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    return sanitized[:63]
```

---

## Version Control

Manage module versions and dependencies within configuration files, such as `default_versions.json`, to ensure consistency across deployments.

```json
{
  "cert_manager": "1.15.3",
  "kubevirt": "1.3.1",
  "new_module": "0.1.0"
}
```

---

## Contributing to the Project

We welcome contributions from the community! Here's how you can help:

- **Report Issues**: If you encounter any bugs or have feature requests, please open an issue on GitHub.

- **Submit Pull Requests**: If you'd like to contribute code, fork the repository and submit a pull request.

- **Improve Documentation**: Help us enhance this guide and other documentation to make it more accessible.

---

## Additional Resources

- **Kargo Project Repository**: [ContainerCraft Kargo on GitHub](https://github.com/ContainerCraft/Kargo)
- **Pulumi Documentation**: [Pulumi Official Docs](https://www.pulumi.com/docs/)
- **Kubernetes Documentation**: [Kubernetes Official Docs](https://kubernetes.io/docs/home/)
- **KubeVirt Documentation**: [KubeVirt Official Docs](https://kubevirt.io/docs/)
