# KubeVirt Module

ContainerCraft Kargo Kubevirt PaaS KubeVirt module.

The `kubevirt` module automates the deployment and configuration of KubeVirt in your Kubernetes environment using [KubeVirt](https://kubevirt.io/). KubeVirt is a Kubernetes-native solution to run and manage virtual machines alongside container workloads. This module simplifies the setup, configuration, and management of KubeVirt components for a seamless virtualization experience within Kubernetes.

---

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Features](#features)
- [Enabling the Module](#enabling-the-module)
- [Configuration](#configuration)
  - [Default Configuration](#default-configuration)
  - [Custom Configuration](#custom-configuration)
- [Module Components](#module-components)
  - [Namespace Creation](#namespace-creation)
  - [KubeVirt Deployment](#kubevirt-deployment)
  - [Custom Resource Creation](#custom-resource-creation)
- [Integration with Kargo PaaS](#integration-with-kargo-paas)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Introduction

This guide provides an overview of the KubeVirt module, instructions on how to enable and configure it, and explanations of its functionality within the Kargo PaaS platform. Whether you're new to Kubernetes, KubeVirt, or ContainerCraft Kargo PaaS, this guide will help you get started.

## Prerequisites

Before deploying the module, ensure the following prerequisites are met:

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/)
- Python 3.6 or higher
- Python dependencies (install via `pip install -r requirements.txt`)
- Kubernetes cluster (with `kubectl` configured)
- Properly configured `kubeconfig` file

---

## Features

- **Automated Deployment**: Deploys KubeVirt using the official operator YAMLs.
- **Version Management**: Supports explicit version pinning or accepts `latest`.
- **Namespace Isolation**: Deploys KubeVirt in a dedicated namespace.
- **Customizable Configuration**: Allows setting overrides for customization, including emulation and feature gates.
- **Metadata Propagation**: Applies global labels and annotations consistently across resources.

---

## Enabling the Module

The KubeVirt module is enabled by default. Customization can be configured in the Pulumi Stack Configuration.

### Example Pulumi Configuration

```yaml
# Pulumi.<stack-name>.yaml

config:
  kubevirt:
    enabled: true # (default: true)
```

Alternatively, you can set configuration values via the Pulumi CLI:

```bash
pulumi config set --path kubevirt.key value
```

---

## Configuration

### Default Configuration

The module comes with sensible defaults to simplify deployment:

- **Namespace**: `kubevirt`
- **Version**: Uses the default version specified in `default_versions.json`
- **Use Emulation**: `false`
- **Labels and Annotations**: Derived from global configurations

### Custom Configuration

You can customize the module's behavior by providing additional configuration options.

#### Available Configuration Options

- **namespace** *(string)*: The namespace where KubeVirt will be deployed.
- **version** *(string)*: The version of the KubeVirt operator YAML to deploy. Use `'latest'` to fetch the latest version.
- **use_emulation** *(bool)*: Whether to enable KVM emulation.
- **labels** *(dict)*: Custom labels to apply to resources.
- **annotations** *(dict)*: Custom annotations to apply to resources.

#### Example Custom Configuration

```yaml
# Pulumi.<stack-name>.yaml
# Default values are shown for reference

config:
  kubevirt:
    enabled: true
    version: "0.43.0"
    namespace: "custom-kubevirt"
    use_emulation: true
    labels:
      app.kubernetes.io/name: "kubevirt"
    annotations:
      organization: "ContainerCraft"
```

---

## Module Components

### Namespace Creation

The module creates a dedicated namespace for KubeVirt to ensure isolation and better management.

- **Namespace**: Configurable via the `namespace` parameter.
- **Labels and Annotations**: Applied as per best practices for identification.

### KubeVirt Deployment

The module deploys KubeVirt using the official operator YAML from the KubeVirt GitHub repository.

- **Operator YAML**: Downloaded from the specified version or the latest release.
- **Custom Values**: Includes configurations for namespaces, labels, and annotations.
- **Version**: Configurable; defaults to the version specified in `default_versions.json`.

### Custom Resource Creation

To manage KubeVirt operational settings, the module creates custom resources with specified configurations.

- **KubeVirt CR**: Customizes KubeVirt to enable emulation and additional feature gates.
- **SMBIOS Configuration**: Adds specific values to the SMBIOS configuration for virtual machines.
- **Namespace and Resources**: The custom resource is applied in the specified namespace with the appropriate labels and annotations.

## Integration with Kargo PaaS

KubeVirt integrates seamlessly with the Kargo Kubevirt PaaS, making it simple to manage and run virtual machines alongside container workloads. The deployment process is optimized for consistency and simplicity, ensuring a smooth user experience within the Kubernetes ecosystem.

---

## Best Practices

- **Namespace Isolation**: Always deploy KubeVirt in a dedicated namespace to avoid conflicts.
- **Version Pinning**: Pin specific versions in production to avoid unintended issues with new releases.
- **Emulation Enablement**: Enable `use_emulation` only if you intend to run KubeVirt on non-bare-metal setups.

---

## Troubleshooting

### Common Issues

- **Connection Errors**: Ensure your `kubeconfig` and Kubernetes context are correctly configured.
- **Version Conflicts**: If deployment fails due to version issues, verify the specified version is available in the KubeVirt repository. Alternatively use `'latest'` and Kargo will fetch the latest version.
- **Namespace Issues**: Ensure the specified namespace is unique or does not conflict with existing namespaces.

### Debugging Steps

1. **Check Pulumi Logs**: Look for error messages during deployment.
2. **Verify Kubernetes Resources**: Use `kubectl` to inspect the KubeVirt namespace and resources.
3. **Review Configuration**: Ensure all configuration options are correctly set in your Pulumi config or remove configuration to use defaults.

---

## Additional Resources

- **KubeVirt Documentation**: [https://kubevirt.io/docs/](https://kubevirt.io/docs/)
- **Kargo Kubevirt PaaS IaC Documentation**: Refer to the main [Kargo README](../README.md) for project usage.
- **Pulumi Kubernetes Provider**: [https://www.pulumi.com/docs/reference/pkg/kubernetes/](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- **Helm Charts**: [https://artifacthub.io/packages/helm/jetstack/cert-manager](https://artifacthub.io/packages/helm/jetstack/cert-manager)
- **Need Help?** If you have questions or need assistance, feel free to reach out to the community or maintainers on GitHub, Discord, or Twitter.
