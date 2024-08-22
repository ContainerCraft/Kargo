---
runme:
  id: 01J5VCA15YC12P0ASQ3CHPQFSZ
  version: v3
shell: /usr/bin/bash
terminalRows: 20
---

# Kargo - The Cloud-Native ESXi Replacement

[![CI - Kargo on Kind](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml/badge.svg)](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml)

## Overview

Kargo replaces traditional hypervisors with a cloud-native container and virtualization platform. Kargo works seamlessly in on-prem, cloud, and local environments, leveraging Kubernetes to create a robust and scalable platform for modern compute and platform as a service use cases.

### Join the Community

Join Kargo users and contributors in the [ContainerCraft Community Discord](https://discord.gg/Jb5jgDCksX)!

For more information, explore the [Kargo Project FAQ](FAQ.md).

![Kargo in Konductor Devcontainer](.github/images/konductor-docker-linux-devcontainer.png?raw=true "Kargo Konductor Codespaces")

> **Note:** Kargo is in the pre-alpha pathfinding stage. Checkout [@usrbinkat](https://twitter.com/usrbinkat)'s [inaugural Twitter/X Thread](https://x.com/usrbinkat/status/1749186949590794551) to learn more.

## Project Goals

- Simplify Kubernetes skills development
- Accelerate project ideation and innovation
- Build a shared platform for community collaboration
- Develop an enterprise-grade hyperconverged compute platform
- Foster community equity through a reliable and inclusive platform
- Bring the power of cloud native to homelabs and students

## Getting Started

Try Kargo with just a browser to get started with [GitHub Codespaces](https://github.com/features/codespaces) following the steps below.

### Prerequisites

Ensure you have the following tools and accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)
3. [Microsoft Edge](https://www.microsoft.com/en-us/edge) or [Google Chrome](https://www.google.com/chrome)

### Quickstart

Check out the video to see Kargo deploy for yourself, or try it in your browser with the steps below.

[![Deploy Kargo Kubevirt PaaS IaC Quickstart](https://img.youtube.com/vi/qo7EfF-xdK0/0.jpg)](https://www.youtube.com/watch?v=qo7EfF-xdK0)

#### Step-by-Step Instructions

1. **Log in to GitHub.**
2. **Launch Kargo in GitHub Codespaces:**

   - Use the [Launch Kargo](https://bit.ly/launch-kargo-kubevirt-paas-in-github-codespaces) link directly or use the green `Code` button above to start a new Codespace.
   - Create a new Codespace with the following options:
     - **Branch:** `main`
     - **Dev Container Configuration:** `konductor`
     - **Region:** Your choice
     - **Machine Type:** 4 cores, 16 GB RAM, or better

3. **Open the VSCode Integrated Terminal:**

   - Use key combination `[ Ctrl + ` ]` to open the terminal.

4. **Log in to Pulumi Cloud:**

```bash {"id":"01J5VC1KTJBR22WEDNSSGTNAX4","name":"login"}
task login
```

5. **Configure the Pulumi Stack:**

```bash {"id":"01J5VC1KTJBR22WEDNSWYBKNQS","name":"configure"}
# confirm Pulumi stack
export DEPLOYMENT=Enter the name of the deployment
export ORGANIZATION=Enter your organization name
export PROJECT="kargo"

source .envrc

task configure
```

6. **Launch Talos-in-Docker Kubernetes:**

```bash {"id":"01J5VC1KTJBR22WEDNSX4RHEG2","name":"kubernetes"}
task kubernetes
```

7. **Deploy Kargo Kubevirt PaaS IaC:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNSZW7QADA","name":"deploy"}
task deploy
```

8. **Deploy a New Kubevirt VM Instance:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT2EWEW9Q","name":"vm"}
# Enable the VM instance
pulumi config set --path vm.enabled true

# Deploy the Kubevirt VM instance
task deploy
```

9. **SSH into the New VM Instance:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT3YSQGM0","name":"ssh"}
ssh -p 30590 -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no kc2@localhost screenfetch
```

10. **Access the VM via `virtctl` SSH:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT6VNC5EK","name":"virtctl-ssh"}
# SSH using virtctl
virtctl ssh kc2@ubuntu
```

11. **Access the VM via `virtctl` Serial Console:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT7BDRMAV","name":"virtctl-console"}
# Serial console access
virtctl console ubuntu
```

> **Tip:** To exit the serial console, press `Ctrl + ]` or close the terminal.

12. **Cleanup:**

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT7BDRMAV","name":"clean"}
task clean-all
```

## Contributing

Kargo thrives on community contributions. Learn how to get involved by reading our [CONTRIBUTING.md](https://github.com/ContainerCraft/Kargo/issues/22).

### Developing Kargo

Use our GitHub Actions integration and the `act` tool to test CI pipelines locally before pushing your changes.

To test Kargo CI locally:

```bash {"excludeFromRunAll":"true","id":"01J5VC1KTJBR22WEDNT92WYZEH"}
task act
```

## Stay Connected

For more discussion, support, and contribution, join our [ContainerCraft Community Discord Kargo Channel](https://discord.gg/Jb5jgDCksX).
