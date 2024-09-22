# Cert Manager Module Guide

Welcome to the **Cert Manager Module** for the Kargo KubeVirt Kubernetes PaaS! This guide is tailored for both newcomers to DevOps and experienced developers, providing a comprehensive overview of how to deploy and configure the Cert Manager module within the Kargo platform.

---

## Table of Contents

- [Introduction](#introduction)
- [Why Use Cert Manager?](#why-use-cert-manager)
- [Getting Started](#getting-started)
- [Enabling the Module](#enabling-the-module)
- [Configuration Options](#configuration-options)
  - [Default Settings](#default-settings)
  - [Customizing Your Deployment](#customizing-your-deployment)
- [Module Components Explained](#module-components-explained)
  - [Namespace Creation](#namespace-creation)
  - [Helm Chart Deployment](#helm-chart-deployment)
  - [Self-Signed Cluster Issuer Setup](#self-signed-cluster-issuer-setup)
- [Using the Module](#using-the-module)
  - [Example Usage](#example-usage)
- [Troubleshooting and FAQs](#troubleshooting-and-faqs)
- [Additional Resources](#additional-resources)
- [Conclusion](#conclusion)

---

## Introduction

The Cert Manager module automates the management of SSL/TLS certificates in your Kubernetes cluster using [cert-manager](https://cert-manager.io/). It simplifies the process of obtaining, renewing, and managing certificates, enhancing the security of your applications without manual intervention.

---

## Why Use Cert Manager?

- **Automation**: Automatically provisions and renews certificates.
- **Integration**: Works seamlessly with Kubernetes Ingress resources and other services.
- **Security**: Enhances security by ensuring certificates are always up-to-date.
- **Compliance**: Helps meet compliance requirements by managing PKI effectively.

---

## Getting Started

### Prerequisites

- **Kubernetes Cluster**: Ensure you have access to a Kubernetes cluster.
- **Pulumi CLI**: Install the Pulumi CLI and configure it.
- **Kubeconfig**: Your kubeconfig file should be properly set up.

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

The Cert Manager module is enabled by default. To verify or modify its enabled status, adjust your Pulumi configuration.

### Verifying Module Enablement

```yaml
# Pulumi.<stack-name>.yaml

config:
  cert_manager:
    enabled: true  # Set to false to disable
```

Alternatively, use the Pulumi CLI:

```bash
pulumi config set --path cert_manager.enabled true
```

---

## Configuration Options

### Default Settings

The module is designed to work out-of-the-box with default settings:

- **Namespace**: `cert-manager`
- **Version**: Defined in `default_versions.json`
- **Cluster Issuer Name**: `cluster-selfsigned-issuer`
- **Install CRDs**: `true`

### Customizing Your Deployment

You can tailor the module to fit your specific needs by customizing its configuration.

#### Available Configuration Parameters

- **enabled** *(bool)*: Enable or disable the module.
- **namespace** *(string)*: Kubernetes namespace for cert-manager.
- **version** *(string)*: Helm chart version to deploy. Use `'latest'` to fetch the most recent stable version.
- **cluster_issuer** *(string)*: Name of the ClusterIssuer resource.
- **install_crds** *(bool)*: Whether to install Custom Resource Definitions.

#### Example Custom Configuration

```yaml
config:
  cert_manager:
    enabled: true
    namespace: "my-cert-manager"
    version: "1.15.3"
    cluster_issuer: "my-cluster-issuer"
    install_crds: true
```

---

## Module Components Explained

### Namespace Creation

A dedicated namespace is created to isolate cert-manager resources.

- **Why?**: Ensures better organization and avoids conflicts.
- **Customizable**: Change the namespace using the `namespace` parameter.

### Helm Chart Deployment

Deploys cert-manager using Helm.

- **Chart Repository**: `https://charts.jetstack.io`
- **Version Management**: Specify a version or use `'latest'`.
- **Custom Values**: Resource requests and limits are set for optimal performance.

### Self-Signed Cluster Issuer Setup

Sets up a self-signed ClusterIssuer for certificate provisioning.

- **Root ClusterIssuer**: Creates a root issuer.
- **CA Certificate**: Generates a CA certificate stored in a Kubernetes Secret.
- **Primary ClusterIssuer**: Issues certificates for your applications using the CA certificate.
- **Exported Values**: CA certificate data is exported for use in other modules.

---

## Using the Module

### Example Usage

After enabling and configuring the module, deploy it using Pulumi:

```bash
pulumi up
```

---

## Troubleshooting and FAQs

**Q1: Cert-manager pods are not running.**

- **A**: Check the namespace and ensure that CRDs are installed. Verify the Kubernetes version compatibility.

**Q2: Certificates are not being issued.**

- **A**: Ensure that the ClusterIssuer is correctly configured and that your Ingress resources reference it.

**Q3: How do I update cert-manager to a newer version?**

- **A**: Update the `version` parameter in your configuration and run `pulumi up`.

---

## Additional Resources

- **cert-manager Documentation**: [cert-manager.io/docs](https://cert-manager.io/docs/)
- **Kargo Project**: [Kargo GitHub Repository](https://github.com/ContainerCraft/Kargo)
- **Pulumi Kubernetes Provider**: [Pulumi Kubernetes Docs](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- **Helm Charts Repository**: [Artifact Hub - cert-manager](https://artifacthub.io/packages/helm/cert-manager/cert-manager)
