# Cert Manager Module for Kargo PaaS

Welcome to the Cert Manager module for the ContainerCraft Kargo PaaS platform! This module automates the deployment and management of certificates in your Kubernetes cluster using [cert-manager](https://cert-manager.io/). It simplifies the process of issuing and renewing SSL/TLS certificates, enhancing the security of your applications.

This guide provides an overview of the Cert Manager module, instructions on how to enable and configure it, and explanations of its functionality within the Kargo PaaS platform. Whether you're new to Kubernetes, cert-manager, or ContainerCraft Kargo PaaS, this guide will help you get started.

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
  - [Helm Chart Deployment](#helm-chart-deployment)
  - [Self-Signed Cluster Issuer](#self-signed-cluster-issuer)
- [Integration with Kargo PaaS](#integration-with-kargo-paas)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)
- [Conclusion](#conclusion)

---

## Introduction

The Cert Manager module automates the installation and configuration of cert-manager in your Kubernetes cluster using Pulumi and the Kargo PaaS platform. By integrating cert-manager, you can easily manage SSL/TLS certificates for your applications, enabling secure communication and compliance with industry standards.

---

## Prerequisites

- **Kubernetes Cluster**: A running Kubernetes cluster accessible via `kubeconfig`.
- **Pulumi Installed**: Ensure Pulumi is installed and configured.
- **Kargo PaaS Setup**: Basic setup of the Kargo PaaS platform.
- **Access to Helm Charts**: Ability to pull Helm charts from `https://charts.jetstack.io`.

---

## Features

- **Automated Deployment**: Installs cert-manager using Helm charts.
- **Version Management**: Supports specific versions or defaults to the latest version.
- **Namespace Isolation**: Deploys cert-manager in a dedicated namespace.
- **Self-Signed Certificates**: Sets up a self-signed ClusterIssuer for certificate management.
- **Customizable Configuration**: Allows overriding default settings to fit your needs.

---

## Enabling the Module

To enable the Cert Manager module, update your Pulumi configuration to include the `cert_manager` section with `enabled: true`.

### Example Pulumi Configuration

```yaml
# Pulumi.<stack-name>.yaml

config:
  cert_manager:
    enabled: true # (default: true)
```

Alternatively, you can set the configuration via the Pulumi CLI:

```bash
pulumi config set --path cert_manager.enabled true
```

---

## Configuration

### Default Configuration

The module comes with sensible defaults to simplify deployment:

- **Namespace**: `cert-manager`
- **Version**: Uses the default version specified in `default_versions.json`
- **Cluster Issuer Name**: `cluster-selfsigned-issuer`
- **Install CRDs**: `true`

### Custom Configuration

You can customize the module's behavior by providing additional configuration options.

#### Available Configuration Options

- **namespace** *(string)*: The namespace where cert-manager will be deployed.
- **version** *(string)*: The version of the cert-manager Helm chart to deploy. Use `'latest'` to fetch the latest version.
- **cluster_issuer** *(string)*: The name of the ClusterIssuer to create.
- **install_crds** *(bool)*: Whether to install Custom Resource Definitions (CRDs).

#### Example Custom Configuration

```yaml
# Pulumi.<stack-name>.yaml

config:
  cert_manager:
    enabled: true
    version: "1.15.3"
    cluster_issuer: "my-cluster-issuer"
    namespace: "custom-cert-manager"
    install_crds: true # (default: true)
```

---

## Module Components

### Namespace Creation

The module creates a dedicated namespace for cert-manager to ensure isolation and better management.

- **Namespace**: Configurable via the `namespace` parameter.
- **Labels and Annotations**: Applied as per best practices for identification.

### Helm Chart Deployment

The module deploys cert-manager using the official Helm chart from Jetstack.

- **Repository**: `https://charts.jetstack.io`
- **Chart Name**: `cert-manager`
- **Version**: Configurable; defaults to the version specified in `default_versions.json`.
- **Custom Values**: Resources and replica counts are configured for optimal performance.

### Self-Signed Cluster Issuer

To enable certificate issuance, the module sets up a self-signed ClusterIssuer.

- **Root ClusterIssuer**: `cluster-selfsigned-issuer-root`
- **CA Certificate**: Generated and stored in a Kubernetes Secret.
- **Primary ClusterIssuer**: Uses the CA certificate to issue certificates for your applications.
- **Secret Export**: The CA certificate data is exported and available for other modules or applications.

---

## Integration with Kargo PaaS

The Cert Manager module integrates seamlessly with the Kargo PaaS platform, leveraging shared configurations and best practices.

- **Version Handling**: Uses centralized version management from `src/lib/versions.py`.
- **Configuration Merging**: Combines user-provided configurations with defaults for consistency.
- **Resource Dependencies**: Manages dependencies between resources to ensure correct deployment order.
- **Exported Outputs**: Provides necessary outputs for other modules or services to consume.

---

## Best Practices

- **Version Specification**: While the module can use the latest version, specifying a version ensures consistency across deployments.
- **CRD Management**: Set `install_crds` to `true` unless CRDs are managed externally.
- **ClusterIssuer Naming**: Use meaningful names for ClusterIssuers to avoid conflicts.
- **Resource Monitoring**: Keep an eye on resource usage, especially if adjusting the default resource requests and limits.

---

## Troubleshooting

### Common Issues

- **Connection Errors**: Ensure your `kubeconfig` and Kubernetes context are correctly configured.
- **Version Conflicts**: If deployment fails due to version issues, verify the specified version is available in the Helm repository.
- **CRD Issues**: If CRDs are not installed, cert-manager components may fail to function properly.

### Debugging Steps

1. **Check Pulumi Logs**: Look for error messages during deployment.
2. **Verify Kubernetes Resources**: Use `kubectl` to inspect the cert-manager namespace and resources.
3. **Review Configuration**: Ensure all configuration options are correctly set in your Pulumi config.

---

## Additional Resources

- **cert-manager Documentation**: [https://cert-manager.io/docs/](https://cert-manager.io/docs/)
- **Kargo PaaS Documentation**: Refer to the main [Kargo README](../README.md) for developer guidelines.
- **Pulumi Kubernetes Provider**: [https://www.pulumi.com/docs/reference/pkg/kubernetes/](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- **Helm Charts**: [https://artifacthub.io/packages/helm/cert-manager/cert-manager](https://artifacthub.io/packages/helm/cert-manager/cert-manager)

---

## Conclusion

The Cert Manager module simplifies the integration of cert-manager into your Kubernetes cluster within the Kargo PaaS platform. By following this guide, you can easily enable and configure the module to enhance the security and reliability of your applications.

**Need Help?** If you have questions or need assistance, feel free to reach out to the community or maintainers.
