# Kargo Kubevirt Kubernetes PaaS - Pulumi Python Infrastructure as Code (IaC)

## **Developer & Architecture Ethos**

> **Prime Directive:** "Features are nice. Quality is paramount."
>
> Quality is not just about the product or code. Enjoyable developer experience is imperative to the survival of FOSS.

ContainerCraft is a Developer Experience (DX) and User Experience (UX) obsessed project. As part of the CCIO Open Source education and skill development ecosystem, the Kargo project's survival is dependent on the happiness of community developers and users.

### **Developer Directives**

- **Improve Code Maintainability**: Enhance structure and organization. Prioritize readable, reusable, and extensible code.
- **Optimize Performance**: Improve code execution performance. Honor configuration. Do not execute inactive code.
- **Establish Standard Practices**: Develop a consistent approach to configuration handling, module deployment, and code organization to guide future development.

---

## **Getting Started**

### **Prerequisites**

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/)
- Python 3.6 or higher
- Python dependencies (install via `pip install -r requirements.txt`)
- Kubernetes cluster (with `kubectl` configured)
- Helm CLI (for Helm-related operations)

### **Setting Up Your Environment**

1. **Clone the repository:**

    ```sh
    git clone https://github.com/containercraft/kargo.git
    cd kargo
    ```

2. **Configure your Pulumi stack:**

    ```sh
    pulumi stack init <stack-name>
    ```

3. **Set up your Pulumi configuration:**

    ```sh
    pulumi config set kubernetes:kubeconfig <path-to-kubeconfig>
    ```

4. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

5. **Deploy the stack:**

    ```sh
    pulumi up
    ```

---

## **Developer Imperatives**

### Detailed Breakdown

1. **User Experience (UX)**
    - **Clear Error Messages:** Provide meaningful error messages that guide users to resolve issues.
    - **Uniform Logging:** Use consistent logging practices to make debugging easier.
      ```python
      pulumi.log.info(f"Deploying module: {module_name}")
      ```

2. **Developer Experience (DX)**
    - **Documentation:** Add comprehensive docstrings and comments.
      ```python
      def deploy_module(...):
          """
          Helper function to deploy a module based on configuration.
          ...
          """
      ```
    - **Examples:** Include example configurations and usage in the documentation.

3. **Configurable Modules**
    - **Pulumi Stack Configuration:** Use the Pulumi config object to roll out custom module configurations.
      ```python
      module_config = config.get_object("module_name") or {}
      ```

4. **Module Data Classes**
    - **Typed Data Classes:** Encapsulate configurations clearly using `dataclass`.
      ```python
      from dataclasses import dataclass
      @dataclass
      class KubeVirtConfig:
          namespace: str = "default"
      ```

5. **Sane Defaults in Data Classes**
    - **Sensible Defaults:** Set reasonable default values to ensure minimal user configuration.
      ```python
      @dataclass
      class CertManagerConfig:
          namespace: str = "cert-manager"
          install_crds: bool = True
      ```

6. **User Configuration Handling**
    - **Merge Configurations:** Combine user-provided configurations with defaults.
      ```python
      @staticmethod
      def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
          default_config = CertManagerConfig()
          for key, value in user_config.items():
              if hasattr(default_config, key):
                  setattr(default_config, key, value)
          return default_config
      ```

7. **Simple Function Signatures**
    - **Reduce Parameters:** Keep function signatures minimal by encapsulating configurations.
      ```python
      def deploy_module(module_config: ModuleConfig)
      ```

8. **Type Annotations**
    - **Enhance Readability:**
      ```python
      def deploy_module(module_name: str, config: pulumi.Config) -> None:
      ```

9. **Safe Function Signatures**
    - **Type Safety:** Use consistent type checks and raise meaningful errors.
      ```python
      if not hasattr(default_config, key):
          pulumi.log.warn(f"Unknown configuration key '{key}' in config.")
      ```

10. **Streamlined Entrypoint**
    - **Minimize Top-Level Code:** Encapsulate logic within the module and related files.
      ```python
      if __name__ == "__main__":
          main()
      ```

11. **Reuse + Dedupe Code**
    - **Central Utilities:** Use common patterns by placing reusable code in `core/utils.py`.
      ```python
      from core.utils import sanitize_label_value, extract_repo_name
      ```

12. **Version Control Dependencies**
    - **Manage Versions:** Control component versions within `versions.py` to maintain consistency.
      ```python
      default_versions = load_default_versions(config)
      ```

13. **Transparency**
    - **Informative Outputs:** Export configuration and version information.
      ```python
      pulumi.export("versions", versions)
      ```

14. **Conditional Execution**
    - **Avoid Unnecessary Execution:** Load and execute only the necessary modules.
      ```python
      if module_enabled:
          deploy_func(...)
      ```

15. **Remove Deprecated Code**
    - **Eliminate Obsolete Features:** Keep the codebase clean and update features as required.

---

## **Developing New Modules**

### **Directory Structure**

Maintain a consistent directory structure for new modules. Below is an example structure:

```
kargo/
README.md
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
        ...
```

### **Creating a New Module**

1. **Define Configuration:**

    Add a new `types.py` file under your module directory to define the configuration dataclass:

    ```python
    from dataclasses import dataclass, field
    from typing import Optional, Dict, Any

    @dataclass
    class NewModuleConfig:
        version: Optional[str] = None
        param1: str = "default_value"
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

2. **Deploy Function:**

    Define the deployment logic in `deploy.py`:

    ```python
    from typing import List, Dict, Any, Tuple, Optional
    import pulumi
    import pulumi_kubernetes as k8s

    from core.types import NamespaceConfig
    from core.namespace import create_namespace
    from core.metadata import get_global_annotations, get_global_labels
    from core.utils import set_resource_metadata
    from .types import NewModuleConfig

    def deploy_new_module(
            config_new_module: NewModuleConfig,
            global_depends_on: List[pulumi.Resource],
            k8s_provider: k8s.Provider,
        ) -> Tuple[Optional[str], Optional[pulumi.Resource]]:
        # Define deployment logic here
        namespace_config = NamespaceConfig(name=config_new_module.namespace)
        namespace_resource = create_namespace(namespace_config, k8s_provider, global_depends_on)

        # Implement specific resource creation and transformation logic
        ...

        return version, deployed_resource
    ```

3. **Update `__main__.py`:**

    Ensure your module is included in the main deployment script:

    ```python
    from typing import List, Dict, Any

    import pulumi
    from pulumi_kubernetes import Provider

    from core.init import initialize_pulumi
    from core.config import export_results
    from core.deploy_module import deploy_module

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

            deploy_modules(modules_to_deploy, config, default_versions, global_depends_on, k8s_provider, versions, configurations)

            compliance_config = init.get("compliance_config", {})
            export_results(versions, configurations, compliance_config)

        except Exception as e:
            pulumi.log.error(f"Deployment failed: {str(e)}")
            raise

    def deploy_modules(
            modules: List[str],
            config: pulumi.Config,
            default_versions: Dict[str, Any],
            global_depends_on: List[pulumi.Resource],
            k8s_provider: Provider,
            versions: Dict[str, str],
            configurations: Dict[str, Dict[str, Any]]
        ) -> None:

        for module_name in modules:
            pulumi.log.info(f"Deploying module: {module_name}")
            deploy_module(
                module_name=module_name,
                config=config,
                default_versions=default_versions,
                global_depends_on=global_depends_on,
                k8s_provider=k8s_provider,
                versions=versions,
                configurations=configurations,
            )

    if __name__ == "__main__":
        main()
    ```

### **Common Utilities**

Refer to `core/utils.py` for common helper functions. For example, `set_resource_metadata` to apply global labels and annotations:

```python
from typing import Optional, Dict, Any
import re
import pulumi
import pulumi_kubernetes as k8s

def set_resource_metadata(metadata: Any, global_labels: Dict[str, str], global_annotations: Dict[str, str]):
    if isinstance(metadata, dict):
        if metadata.get('labels') is None:
            metadata['labels'] = {}
        metadata.setdefault('labels', {}).update(global_labels)

        if metadata.get('annotations') is None:
            metadata['annotations'] = {}
        metadata.setdefault('annotations', {}).update(global_annotations)

    elif isinstance(metadata, k8s.meta.v1.ObjectMetaArgs):
        if metadata.labels is None:
            metadata.labels = {}
        metadata.labels.update(global_labels)

        if metadata.annotations is None:
            metadata.annotations = {}
        metadata.annotations.update(global_annotations)

def sanitize_label_value(value: str) -> str:
    value = value.lower()
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    return sanitized[:63]
```

### **Version Control**

Manage module versions within `core/versions.py`:

```python
import json
import os
import pulumi
import requests

DEFAULT_VERSIONS_URL_TEMPLATE = 'https://raw.githubusercontent.com/ContainerCraft/Kargo/rerefactor/pulumi/'

def load_default_versions(config: pulumi.Config, force_refresh=False) -> dict:
    ...
    # Function implementation
    ...
```
