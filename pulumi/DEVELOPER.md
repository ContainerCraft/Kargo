## **Developer & Architecture Ethos**

Kargo Kubevirt Kubernetes PaaS - Pulumi Python Infrastructure as Code (IaC)

> Prime Directive: "Features are nice. Quality is paramount."
>
> Quality is not just about the product or code. Enjoyable developer experience is imperative to the survival of FOSS.

#### **Developer Directives**
- **Improve Code Maintainability:** Enhance structure and organization. Prioritize readable, reusable, and extensible code.
- **Optimize Performance:** Code execution performance. honor configuration. Do not execute inactive code.
- **Establish Standard Practices:** Develop a consistent approach to configuration handling, module deployment, and code organization to guide future development.

---

### **Developer Imperatives**

ContainerCraft is a Developer Experience (DX) and User Experience (UX) obsessed project. As part of the CCIO Open Source education and skill development ecosystem, Kargo project's survival is dependent on the happiness of community developers and users.

The following guidelines promote happiness as a means of promoting growth and sustainability.

| **Imperative** | **Explanation** |
|--------------------------|-------------------------------------------------------------------------------------------------------|
| **User Experience (UX)** | Provide clear error messages, and logging to improve intuitive learning, development, and debugging. |
| **Developer Experience (DX)** | Optimize DX with clear documentation, examples, and architecture. |
| **Configurable Modules** | Support user module customization via the pulumi stack configuration pattern. |
| **Module Data Classes** | Utilize typed dataclasses to safely encapsulate module configuration. |
| **Sane Defaults in Data Classes** | Include sensible default values for module configurations. |
| **User Configuration Handling** | Merge user-provided configurations with defaults. Allow minimal input for module configuration. |
| **Simple Function Signatures** | Reduce parameter count. Encapsulate configuration objects in function signatures. |
| **Type Annotations** | Enhance readability and maintainability with type annotations. |
| **Safe Function Signatures** | Enforce type safety. Raise unknown configuration keys gracefully. |
| **Maintain a streamlined entrypoint** | Minimize top-level code. Encapsulate module logic within the module directory and code. |
| **Reuse + Dedupe code** | Refactor common patterns and logic into shared utilities in `src/lib/`. Adopt shared utilities when possible. |
| **Version Control Dependencies** | Utilize `versions.py` to manage component versions within `__main__.py`. |
| **Transparency** | Return informative version and configuration values to `version` and `configuration` dictionaries. |
| **Conditional Execution** | Use conditional imports and execution. Prevent unnecessary code execution when modules are disabled. |
| **Remove Deprecated Code** | Eliminate deprecated feature code. |

---

### **Detailed Breakdown**

**TODO**: Add detailed breakdown of each imperative and explanation with code snippet examples and links to exemplary code.
