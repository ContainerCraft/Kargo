# Cert Manager Module

ContainerCraft Kargo Kubevirt PaaS Cert Manager module.

The `cert_manager` module automates SSL certificates and certificate issuers in your platform using [cert-manager](https://cert-manager.io/). Cert Manager is a dependency of many components in Kargo Kubevirt PaaS including Containerized Data Importer, Kubevirt, Hostpath Provisioner, and more. Cert Manager improves the simplicity of issuing and renewing SSL/TLS certificates making PKI (Private Key Infrastructure) an integrated and automated feature of the platform.

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

This guide provides an overview of the Cert Manager module, instructions on how to enable and configure it, and explanations of its functionality within the Kargo PaaS platform. Whether you're new to Kubernetes, cert-manager, or ContainerCraft Kargo PaaS, this guide will help you get started.

---

## Features

- **Automated Deployment**: Installs cert-manager using Helm charts.
- **Version Management**: Supports explicit version pinning or accepts `latest`.
- **Namespace Isolation**: Deploys cert-manager in a dedicated namespace.
- **Self-Signed Certificates**: Sets up a self-signed ClusterIssuer for certificate management.
- **Customizable Configuration**: Allows setting overrides for customization.

---

## Enabling the Module

The Cert Manager module is enabled by default and executes with sane defaults. Customization can be configured in the Pulumi Stack Configuration.

### Example Pulumi Configuration

```yaml
# Pulumi.<stack-name>.yaml

config:
  cert_manager:
    enabled: true # (default: true)
```

Alternatively, you can set configuration values via the Pulumi CLI:

```bash
pulumi config set --path cert_manager.key value
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
# Default values are shown for reference

config:
  cert_manager:
    enabled: true
    version: "1.15.3"
    cluster_issuer: "my-cluster-issuer"
    namespace: "custom-cert-manager"
    install_crds: true
```

---

## Module Components

### Namespace Creation

The module creates a dedicated namespace for cert-manager to ensure isolation and better management.

- **Namespace**: Configurable via the `namespace` parameter.
- **Labels and Annotations**: Applied as per best practices for identification.

### Helm Chart Deployment

The module deploys cert-manager using the official Helm chart from Jetstack.

- **Chart Name**: `cert-manager`
- **Repository**: `https://charts.jetstack.io`
- **Custom Values**: Resources and replica counts are configured for optimal performance.
- **Version**: Configurable; defaults to the version specified in `default_versions.json`.

### Self-Signed Cluster Issuer

To enable self signed local certificates, the module includes a self-signed ClusterIssuer chain of trust.

- **Root ClusterIssuer**: `cluster-selfsigned-issuer-root`
- **CA Certificate**: Generated and stored in a Kubernetes Secret.
- **Primary ClusterIssuer**: Uses the CA certificate to issue certificates for your applications.
- **Secret Export**: The CA certificate data is exported and available for other modules or applications.

## Troubleshooting

### Common Issues

- **Connection Errors**: Ensure your `kubeconfig` and Kubernetes context are correctly configured.
- **Version Conflicts**: If deployment fails due to version issues, verify the specified version is available in the Helm repository. Alternatively use `'latest'` and Kargo will fetch the latest version.
- **CRD Issues**: If `install_crds` is set to false and are not otherwise installed, cert-manager components may fail install or function properly.

### Debugging Steps

1. **Check Pulumi Logs**: Look for error messages during deployment.
2. **Verify Kubernetes Resources**: Use `kubectl` to inspect the cert-manager namespace and resources.
3. **Review Configuration**: Ensure all configuration options are correctly set in your Pulumi config or remove configuration to use defaults.

---

## Additional Resources

- **cert-manager Documentation**: [https://cert-manager.io/docs/](https://cert-manager.io/docs/)
- **Kargo Kubevirt PaaS IaC Documentation**: Refer to the main [Kargo README](../README.md) for developer guidelines.
- **Pulumi Kubernetes Provider**: [https://www.pulumi.com/docs/reference/pkg/kubernetes/](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- **Helm Charts**: [https://artifacthub.io/packages/helm/cert-manager/cert-manager](https://artifacthub.io/packages/helm/cert-manager/cert-manager)
- **Need Help?** If you have questions or need assistance, feel free to reach out to the community or maintainers on GitHub, Discord, or Twitter.
