# How To: deploy on Kind in Codespaces

1. launch codespaces from Kargo repository
2. open a terminal
3. run the following commands for minimum viable deployment of Kargo IaC:

```bash
# Login to pulumi
pulumi login

# Create Kind K8s Cluster
make kind

# Configure Kargo
pulumi config set kubernetes.kubeconfig $PATH
pulumi config set cilium.enabled true

# Deploy Kargo
pulumi up
```

---

## Additional Modules

### Cilium

```bash
# Enable Cilium
pulumi config set cilium.enabled true

# Set Cilium version
pulumi config set cilium.version 1.14.7
```

### Cert Manager

```bash
# Enable Cert Manager
pulumi config set cert_manager.enabled true

# Set Cert Manager version
pulumi config set cert-manager.version 1.15.1
```

### Kubevirt

```bash
# Enable Kubevirt
pulumi config set --path kubevirt.enabled true

# Set Kubevirt version
pulumi config set --path kubevirt.version 1.2.2
```

### Multus

```bash
# Enable Multus
pulumi config set --path multus.enabled true

# Set Multus version
pulumi config set --path multus.version master

# Set Multus Default Bridge Name for Network Attachment Definition
pulumi config set --path multus.default_bridge br0
```
