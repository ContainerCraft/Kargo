## **Developer & Architecture Ethos**

Kargo Kubevirt Kubernetes PaaS - Pulumi Python Infrastructure as Code (IaC)

> Prime Directive: "Features are nice. Quality is paramount."

> Quality is not just about the product or code. Enjoyable developer experience is imperative to the survival of FOSS.

ContainerCraft is a Developer Experience (DX) and User Experience (UX) obsessed project. As part of the CCIO Open Source education and skill development ecosystem, the Kargo project's survival is dependent on the happiness of community developers and users.

### **Developer Directives**

- **Improve Code Maintainability:** Enhance structure and organization. Prioritize readable, reusable, and extensible code.
- **Optimize Performance:** Improve code execution performance. Honor configuration. Do not execute inactive code.
- **Establish Standard Practices:** Develop a consistent approach to configuration handling, module deployment, and code organization to guide future development.

---

### **Developer Imperatives**

The following guidelines promote happiness as a means of promoting growth and sustainability.

| **Imperative**             | **Explanation**                                                                                  |
|----------------------------|--------------------------------------------------------------------------------------------------|
| **User Experience (UX)**   | Provide clear error messages and logging to improve intuitive learning, development, and debugging. |
| **Developer Experience (DX)** | Optimize DX with clear documentation, examples, and architecture.                               |
| **Configurable Modules**   | Support user module customization via the Pulumi stack configuration pattern.                    |
| **Module Data Classes**    | Utilize typed dataclasses to safely encapsulate module configuration.                            |
| **Sane Defaults in Data Classes** | Include sensible default values for module configurations.                                 |
| **User Configuration Handling** | Merge user-provided configurations with defaults. Allow minimal input for module configuration. |
| **Simple Function Signatures** | Reduce parameter count. Encapsulate configuration objects in function signatures.             |
| **Type Annotations**       | Enhance readability and maintainability with type annotations.                                   |
| **Safe Function Signatures** | Enforce type safety. Raise unknown configuration keys gracefully.                              |
| **Maintain a streamlined entrypoint** | Minimize top-level code. Encapsulate module logic within the module directory and code. |
| **Reuse + Dedupe code**    | Refactor common patterns and logic into shared utilities in `core/utils.py`. Adopt shared utilities when possible. |
| **Version Control Dependencies** | Utilize `versions.py` to manage component versions within `__main__.py`.                     |
| **Transparency**           | Return informative version and configuration values to `version` and `configuration` dictionaries. |
| **Conditional Execution**  | Use conditional imports and execution. Prevent unnecessary code execution when modules are disabled. |
| **Remove Deprecated Code** | Eliminate deprecated feature code.                                                                |

---

### **Detailed Breakdown**

1. **User Experience (UX):**
    - **Clear Error Messages:** Provide meaningful error messages that guide users to resolve issues.
    - **Uniform Logging:** Use consistent logging practices to make debugging easier. For instance:
      ```python
      pulumi.log.info(f"Deploying module: {module_name}")
      ```

2. **Developer Experience (DX):**
    - **Documentation:** Add comprehensive docstrings and comments. For instance:
      ```python
      def deploy_module(...):
          """
          Helper function to deploy a module based on configuration.
          ...
          """
      ```
    - **Examples:** Include example configurations and usage in the documentation.

3. **Configurable Modules:**
    - **Pulumi Stack Configuration:** Use the Pulumi config object to roll out custom module configurations.
    - **Example:**
      ```python
      module_config = config.get_object("module_name") or {}
      ```

4. **Module Data Classes:**
    - **Typed Data Classes:** Encapsulate configurations clearly using `dataclass`. Example:
      ```python
      from dataclasses import dataclass
      @dataclass
      class KubeVirtConfig:
          namespace: str = "default"
      ```

5. **Sane Defaults in Data Classes:**
    - **Sensible Defaults:** Set reasonable default values to ensure minimal user configuration.
    - **Example:**
      ```python
      @dataclass
      class CertManagerConfig:
          namespace: str = "cert-manager"
          install_crds: bool = True
      ```

6. **User Configuration Handling:**
    - **Merge Configurations:** Combine user-provided configurations with defaults. Example:
      ```python
      @staticmethod
      def merge(user_config: Dict[str, Any]) -> 'CertManagerConfig':
          default_config = CertManagerConfig()
          for key, value in user_config.items():
              if hasattr(default_config, key):
                  setattr(default_config, key, value)
          return default_config
      ```

7. **Simple Function Signatures:**
    - **Reduce Parameters:** Keep function signatures minimal by encapsulating configurations.
    - **Example:**
      ```python
      def deploy_module(module_config: ModuleConfig)
      ```

8. **Type Annotations:**
    - **Enhance Readability:**
      ```python
      def deploy_module(module_name: str, config: pulumi.Config) -> None:
      ```

9. **Safe Function Signatures:**
    - **Type Safety:** Use consistent type checks and raise meaningful errors. Example:
      ```python
      if not hasattr(default_config, key):
          pulumi.log.warn(f"Unknown configuration key '{key}' in config.")
      ```

10. **Streamlined Entrypoint:**
    - **Minimize Top-Level Code:** Encapsulate logic within the module and related files. Example:
      ```python
      if __name__ == "__main__":
          main()
      ```

11. **Reuse + Dedupe Code:**
    - **Central Utilities:** Use common patterns by placing reusable code in `core/utils.py`.
    - **Example:**
      ```python
      from core.utils import sanitize_label_value, extract_repo_name
      ```

12. **Version Control Dependencies:**
    - **Manage Versions:** Control component versions within `versions.py` to maintain consistency.
    - **Example:**
      ```python
      default_versions = load_default_versions(config)
      ```

13. **Transparency:**
    - **Informative Outputs:** Export configuration and version information.
    - **Example:**
      ```python
      pulumi.export("versions", versions)
      ```

14. **Conditional Execution:**
    - **Avoid Unnecessary Execution:** Load and execute only the necessary modules.
    - **Example:**
      ```python
      if module_enabled:
          deploy_func(...)
      ```

15. **Remove Deprecated Code:**
    - **Eliminate Obsolete Features:** Keep the codebase clean and update features as required.
