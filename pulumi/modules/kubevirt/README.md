# KubeVirt Module Guide

Welcome to the **KubeVirt Module** for the Kargo KubeVirt Kubernetes PaaS! This guide is intended to help both newcomers and experienced developers understand, deploy, and customize the KubeVirt module within the Kargo platform.

---

## Table of Contents

- [Introduction](#introduction)
- [Why Use KubeVirt?](#why-use-kubevirt)
- [Getting Started](#getting-started)
- [Enabling the Module](#enabling-the-module)
- [Configuration Options](#configuration-options)
  - [Default Settings](#default-settings)
  - [Customizing Your Deployment](#customizing-your-deployment)
- [Module Components Explained](#module-components-explained)
  - [Namespace Creation](#namespace-creation)
  - [Operator Deployment](#operator-deployment)
  - [Custom Resource Configuration](#custom-resource-configuration)
- [Using the Module](#using-the-module)
  - [Example Usage](#example-usage)
- [Troubleshooting and FAQs](#troubleshooting-and-faqs)
- [Additional Resources](#additional-resources)
- [Conclusion](#conclusion)

---

## Introduction

The KubeVirt module enables you to run virtual machines (VMs) within your Kubernetes cluster using [KubeVirt](https://kubevirt.io/). It bridges the gap between containerized applications and traditional VM workloads, providing a unified platform for all your infrastructure needs.

---

## Why Use KubeVirt?

- **Unified Platform**: Manage containers and VMs in a single Kubernetes cluster.
- **Flexibility**: Run legacy applications alongside cloud-native ones.
- **Scalability**: Leverage Kubernetes scaling features for VMs.
- **Ecosystem Integration**: Use Kubernetes tools and practices for VM management.

---

## Getting Started

### Prerequisites

- **Kubernetes Cluster**: Access to a cluster with appropriate resources.
- **Pulumi CLI**: Installed and configured.
- **Kubeconfig**: Properly set up for cluster access.

### Setup Steps

1. **Navigate to the Kargo Pulumi Directory**:
   ```bash
   cd Kargo/pulumi
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Initialize Pulumi Stack**:
   ```bash
   pulumi stack init dev
   ```

---

## Enabling the Module

The KubeVirt module is enabled by default. To confirm or adjust its status, modify your Pulumi configuration.

### Verifying Module Enablement

```yaml
# Pulumi.<stack-name>.yaml

config:
  kubevirt:
    enabled: true  # Set to false to disable
```

Alternatively, use the Pulumi CLI:

```bash
pulumi config set --path kubevirt.enabled true
```

---

## Configuration Options

### Default Settings

- **Namespace**: `kubevirt`
- **Version**: Defined in `default_versions.json`
- **Use Emulation**: `false` (suitable for bare-metal environments)

### Customizing Your Deployment

#### Available Configuration Parameters

- **enabled** *(bool)*: Enable or disable the module.
- **namespace** *(string)*: Kubernetes namespace for KubeVirt.
- **version** *(string)*: Specific version to deploy. Use `'latest'` for the most recent stable version.
- **use_emulation** *(bool)*: Enable if running in a nested virtualization environment.
- **labels** *(dict)*: Custom labels for resources.
- **annotations** *(dict)*: Custom annotations for resources.

#### Example Custom Configuration

```yaml
config:
  kubevirt:
    enabled: true
    namespace: "kubevirt"
    version: "1.3.1"
    use_emulation: true
    labels:
      app: "kubevirt"
    annotations:
      owner: "dev-team"
```

---

## Module Components Explained

### Namespace Creation

A dedicated namespace is created for KubeVirt.

- **Purpose**: Isolates KubeVirt resources for better management.
- **Customization**: Change using the `namespace` parameter.

### Operator Deployment

Deploys the KubeVirt operator.

- **Source**: Official KubeVirt operator YAML.
- **Version Management**: Specify a version or use `'latest'`.
- **Transformation**: YAML is adjusted to fit the specified namespace.

### Custom Resource Configuration

Defines the KubeVirt CustomResource to configure KubeVirt settings.

- **Emulation Mode**: Controlled by `use_emulation`.
- **Feature Gates**: Enables additional features like `HostDevices` and `ExpandDisks`.
- **SMBIOS Configuration**: Sets metadata for virtual machines.

---

## Using the Module

### Example Usage

Deploy the module with your custom configuration:

```bash
pulumi up
```

---

## Troubleshooting and FAQs

**Q1: Virtual machines are not starting.**

- **A**: Ensure that your nodes support virtualization. If running in a VM without the `/dev/kvm` device, set `use_emulation` to `true`.

**Q2: Deployment fails with version errors.**

- **A**: Verify that the specified version exists. Use `'latest'` to automatically fetch the latest stable version.

**Q3: How do I enable additional feature gates?**

- **A**: Modify the `featureGates` section in the `deploy.py` or submit a feature request to expose this via configuration.

---

## Additional Resources

- **KubeVirt Documentation**: [kubevirt.io/docs](https://kubevirt.io/docs/)
- **Kargo Project**: [Kargo GitHub Repository](https://github.com/ContainerCraft/Kargo)
- **Pulumi Kubernetes Provider**: [Pulumi Kubernetes Docs](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- **KubeVirt Releases**: [KubeVirt GitHub Releases](https://github.com/kubevirt/kubevirt/releases)
