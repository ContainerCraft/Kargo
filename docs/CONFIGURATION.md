
This document provides information on the configuration options available for the Kargo Pulumi IaC project.

## Table of Contents

- [Usage](#usage)
- [Configuration](#configuration)
  - [Default Values](#default-values)
  - [General Configuration](#general-configuration)
  - [Module Configurations](#module-configurations)
    - [Cilium Configuration](#cilium-configuration)
    - [Cert Manager Configuration](#cert-manager-configuration)
    - [KubeVirt Configuration](#kubevirt-configuration)
    - [Containerized Data Importer (CDI) Configuration](#containerized-data-importer-cdi-configuration)
    - [Multus Configuration](#multus-configuration)
    - [Cluster Network Addons Operator (CNAO) Configuration](#cluster-network-addons-operator-cnao-configuration)
    - [Hostpath Provisioner Configuration](#hostpath-provisioner-configuration)
    - [Prometheus Configuration](#prometheus-configuration)
    - [Kubernetes Dashboard Configuration](#kubernetes-dashboard-configuration)
    - [OpenUnison Configuration](#openunison-configuration)
    - [Rook Ceph Configuration](#rook-ceph-configuration)
    - [KubeVirt Manager Configuration](#kubevirt-manager-configuration)
  - [Example Commands](#example-commands)

## Usage

To deploy your infrastructure with the specified configurations, follow these steps:

1. **Login and create Pulumi Stack**:
    ```sh
    pulumi login
    pulumi stack select --create <stack-name>
    ```

2. **Set the Configuration Values**:
   Use the `pulumi config set --path` command to set the configuration values as needed. Minimum required configuration values are the path to the kubeconfig file. For example:
   ```sh
   pulumi config set --path kubernetes.kubeconfig $CODESPACE_VSCODE_FOLDER/.kube/config
   ```

3. **Preview the Deployment**:
   ```sh
   pulumi preview
   ```

4. **Deploy the Infrastructure**:
   ```sh
   pulumi up
   ```

5. **Destroy the Infrastructure**:
   When you are done, you can destroy the deployed infrastructure with:
   ```sh
   pulumi destroy
   ```

## Configuration

The minimum viable configuration required for Kargo IaC should look something as follows:

```sh
# Showing a minimum viable configuration for the Pulumi Stack named 'ci'
❯ cat pulumi/stacks/Pulumi.ci.yaml
config:
  kargo:kubernetes:
    kubeconfig: /workspaces/Kargo/.kube/config
```

### Default Values

The following table summarizes the default values for the configuration options if they are not explicitly set:

| Configuration Path                        | Default Value                  |
|-------------------------------------------|--------------------------------|
| `kubernetes.context`                      | `kind-kargo`                   |
| `kubernetes.distribution`                 | `kind`                         |
| `cilium.enabled`                          | `false`                        |
| `cilium.l2announcements`                  | `192.168.1.70/28`              |
| `cilium.l2_bridge_name`                   | `br0`                          |
| `cert_manager.enabled`                    | `false`                        |
| `kubevirt.enabled`                        | `false`                        |
| `cdi.enabled`                             | `false`                        |
| `multus.enabled`                          | `false`                        |
| `multus.version`                          | `master`                       |
| `multus.bridge_name`                      | `br0`                          |
| `cnao.enabled`                            | `false`                        |
| `hostpath_provisioner.enabled`            | `false`                        |
| `hostpath_provisioner.default_path`       | `/var/mnt`                     |
| `hostpath_provisioner.default_storage_class`| `false`                      |
| `prometheus.enabled`                      | `false`                        |
| `kubernetes_dashboard.enabled`            | `false`                        |
| `openunison.enabled`                      | `false`                        |
| `openunison.dns_suffix`                   | `kargo.arpa`                   |
| `openunison.cluster_issuer`               | `cluster-selfsigned-issuer-ca` |
| `ceph.enabled`                            | `false`                        |
| `kubevirt_manager.enabled`                | `false`                        |
### General Configuration

- **Kubernetes Configuration**:
  - `kubernetes.kubeconfig`: Path to the kubeconfig file.
  - `kubernetes.context`: Kubernetes context to use (default: `kind-kargo`).
  - `kubernetes.distribution`: Kubernetes distribution to use (default: `kind`).

### Module Configurations

- **Cilium Configuration**:
  - `cilium.enabled`: Enable or disable the deployment of Cilium (default: `false`).
  - `cilium.version`: Version of Cilium to deploy (optional).
  - `cilium.l2announcements`: L2 announcements for Cilium (default: `192.168.1.70/28`).
  - `cilium.l2_bridge_name`: L2 bridge name for Cilium (default: `br0`).

- **Cert Manager Configuration**:
  - `cert_manager.enabled`: Enable or disable the deployment of Cert Manager (default: `false`).
  - `cert_manager.version`: Version of Cert Manager to deploy (optional).

- **KubeVirt Configuration**:
  - `kubevirt.enabled`: Enable or disable the deployment of KubeVirt (default: `false`).
  - `kubevirt.version`: Version of KubeVirt to deploy (optional).

- **Containerized Data Importer (CDI) Configuration**:
  - `cdi.enabled`: Enable or disable the deployment of CDI (default: `false`).
  - `cdi.version`: Version of CDI to deploy (optional).

- **Multus Configuration**:
  - `multus.enabled`: Enable or disable the deployment of Multus (default: `false`).
  - `multus.version`: Version of Multus to deploy (default: `master`).
  - `multus.bridge_name`: Bridge name for Multus (default: `br0`).

- **Cluster Network Addons Operator (CNAO) Configuration**:
  - `cnao.enabled`: Enable or disable the deployment of CNAO (default: `false`).
  - `cnao.version`: Version of CNAO to deploy (optional).

- **Hostpath Provisioner Configuration**:
  - `hostpath_provisioner.enabled`: Enable or disable the deployment of Hostpath Provisioner (default: `false`).
  - `hostpath_provisioner.version`: Version of Hostpath Provisioner to deploy (optional).
  - `hostpath_provisioner.default_path`: Default path for Hostpath Provisioner (default: `/var/mnt`).
  - `hostpath_provisioner.default_storage_class`: Set as default storage class (default: `false`).

- **Prometheus Configuration**:
  - `prometheus.enabled`: Enable or disable the deployment of Prometheus (default: `false`).
  - `prometheus.version`: Version of Prometheus to deploy (optional).

- **Kubernetes Dashboard Configuration**:
  - `kubernetes_dashboard.enabled`: Enable or disable the deployment of Kubernetes Dashboard (default: `false`).
  - `kubernetes_dashboard.version`: Version of Kubernetes Dashboard to deploy (optional).

- **OpenUnison Configuration**:
  - `openunison.enabled`: Enable or disable the deployment of OpenUnison (default: `false`).
  - `openunison.version`: Version of OpenUnison to deploy (optional).
  - `openunison.dns_suffix`: DNS suffix for OpenUnison (default: `kargo.arpa`).
  - `openunison.cluster_issuer`: Cluster issuer for OpenUnison (default: `cluster-selfsigned-issuer-ca`).
  - `openunison.github.teams`: GitHub teams for OpenUnison authentication.
  - `openunison.github.client_id`: GitHub client ID for OpenUnison authentication.
  - `openunison.github.client_secret`: GitHub client secret for OpenUnison authentication.

- **Rook Ceph Configuration**:
  - `ceph.enabled`: Enable or disable the deployment of Rook Ceph (default: `false`).

- **KubeVirt Manager Configuration**:
  - `kubevirt_manager.enabled`: Enable or disable the deployment of KubeVirt Manager (default: `false`).

### Example Commands

To set these configuration options, you can use the `pulumi config set --path` command. Below are some examples:

- **Set the Kubernetes Kubeconfig Path**:
  ```sh
  pulumi config set --path kubernetes.kubeconfig /path/to/kubeconfig
  ```

- **Enable Cilium Deployment**:
  ```sh
  pulumi config set --path cilium.enabled true
  ```

- **Set the Version for Cert Manager**:
  ```sh
  pulumi config set --path cert_manager.version 1.5.3
  ```

- **Configure L2 Announcements for Cilium**:
  ```sh
  pulumi config set --path cilium.l2announcements 192.168.1.70/28
  ```

- **Enable Kubernetes Dashboard**:
  ```sh
  pulumi config set --path kubernetes_dashboard.enabled true
  ```

- **Set OpenUnison GitHub Client ID**:
  ```sh
  pulumi config set --path openunison.github.client_id your-github-client-id
  ```

- **Enable Rook Ceph Deployment**:
  ```sh
  pulumi config set --path ceph.enabled true
  ```

- **Set Hostpath Provisioner Default Path**:
  ```sh
  pulumi config set --path hostpath_provisioner.default_path /var/lib/k8s
  ```

- **Enable Prometheus Deployment**:
  ```sh
  pulumi config set --path prometheus.enabled true
  ```
