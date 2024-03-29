# Kargo Community Homelab Platform Engineering

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ContainerCraft/Kargo)

[![CI - Kargo on Kind](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml/badge.svg)](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml)

Join the conversation on the [ContainerCraft Community Discord Kargo Channel](https://discord.gg/Jb5jgDCksX).

> Kargo Project opened in the [Konductor Devcontainer](https://github.com/ContainerCraft/Konductor) with Github Codespaces.
> ![Screenshot of Kargo open in Konductor Devcontainer](.github/images/konductor-codespaces.png?raw=true "Kargo Konductor Codespaces")
> NOTE: This project is in pre-alpha pathfinding mode. See the [inaugural Twitter/X Thread post](https://x.com/usrbinkat/status/1749186949590794551) by [@usrbinkat](https://twitter.com/usrbinkat)

## About

Kargo is a community project to build the first Platform Engineered Homelab for the ContainerCraft community. The project is a collaboration between the ContainerCraft community and the Kubernetes industry leaders and practitioners to build a common sharable platform for learning, experimentation, and collaboration.

For more information, see the [Kargo Project FAQ](FAQ.md).

### Goals

- Eliminate the barrier to entry for learning Kubernetes and Cloud Native technologies
- Provide a common platform for the community to collaborate and share knowledge
- Enable anyone to experience the power of owning a local cloud platform
- Accelerate the time-to-achievement for new projects and ideas
- Develop a community library of sharable middleware and application IaC for use on Kargo
- Select enterprise grade technologies and practices to build a valuable learning platform
- Be the best hypervisor and container platform for the Homelab community

### Non-Goals

- Kargo is not a production platform
- Kargo will not try to be everything for everyone

## Getting Started

### Prerequisites

Success with Kargo depends on two things, the server side infrastructure, and the client side tooling. Kargo is the server side platform, and the client side tooling is distributed via the [ContainerCraft Konductor](https://github.com/ContainerCraft/Konductor) devcontainer.

#### Client Side Cloud Dependencies

If running in Github Codespaces, all you need is a browser and a Github account!

#### Client Side Local Dependencies

If running locally on your own machine, you will need the following:

- [Visual Studio Code](https://code.visualstudio.com/)
- [Visual Studio Code Remote - Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Pulumi Cloud Login & Access Token from app.pulumi.com](https://app.pulumi.com/)
  - [Pulumi Cloud PAT Docs](https://www.pulumi.com/docs/pulumi-cloud/access-management/access-tokens/)

After installing VSCode, the Remote Containers extension, and Docker Desktop, you can proceed to clone the Kargo repository and open it in VSCode with this one-liner:

```bash
git clone https://github.com/ContainerCraft/Kargo && cd Kargo && code .
```

When prompted, click "Reopen in Container" to open the Kargo repository in the Konductor devcontainer.

#### Server Side Dependencies

There are two ways to run the server side infrastructure for Kargo. Choose between running, testing, and developing Kargo using [Kind](https://kind.sigs.k8s.io/) from within the Konductor container, or running Kargo on a local or remote [Sidero Talos Kubernetes](https://talos.dev/) cluster.

##### Virtual Kind Kubernetes

Using Kind is the easiest way to get started with Kargo. Kind is a Kubernetes-in-Docker platform that allows you to run a Kubernetes cluster on your local machine. Kind allows for easy testing and development of Kubernetes and Kargo and is the recommended first step for new Kargonauts to familiarize yourself with the project before investing in and provisioning physical hardware.

Kind is also used by the Kargo maintainers and contributors to develop and test Kargo.

##### Physical Talos Kubernetes

[Talos](https://talos.dev/) is a modern OS for Kubernetes. Talos is designed to be secure, immutable, and minimal. Talos is the recommended platform for running Kargo in a production-like homelab environment. Find out more about why in our [FAQ](FAQ.md).

The Talos documentation and deployment automation is still a work in progress under discovery in the [./metal directory](./metal/3node-optiplex-cluster) of this repository. Find the README with current build notes and example configs there.

### How to Run Kargo on Kind

> NOTE: the following assumes you have already installed VSCode, the Remote Containers extension, and Docker Desktop.

1. Clone the Kargo repository to your local machine
2. Open the Kargo repository in VSCode
3. When prompted, click "Reopen in Container" to open the Kargo repository in the Konductor devcontainer
4. Login to Pulumi and configure a new pulumi stack for Kargo

> NOTE: substitute your kubecontext name for `kind-kargo` if you are using a different kubecontext.

```bash
# Setup Pulumi CLI
pulumi login
pulumi install
pulumi stack select --create kind-kargo

# Configure Kargo Stack
pulumi config set kubernetes kind
pulumi config set kubecontext kind-kargo
```

5. Start a local Kind cluster

```bash
make kind
```

6. Once the Kind cluster is running, you can validate access the Kubernetes API with the following command:

```bash
kubectl cluster-info
```

7. Deploy the Kargo platform to the Kind cluster with the following commands:

```bash
# Deploy Kargo
pulumi up
```

7. Test with a VM!

```bash
kubectl apply -f hack/ubuntu-nat.yaml
```

This vm will take a while to start in emulator mode if testing on Kind. You can check the status of the VM with the following command:

```bash
# Connect to the console of the VM
virtctl console ubuntu

# use ssh to connect to the VM
# user:pass == [kc2:kc2]
virtctl ssh kc2@ubuntu
```

## Contributing

Kargo is a community project and we welcome contributions from everyone. Please see [CONTRIBUTING.md](https://github.com/ContainerCraft/Kargo/issues/22) for more information on how to get involved.

To get started, join the conversation on the [ContainerCraft Community Discord Kargo Channel](https://discord.gg/Jb5jgDCksX).

### Developing Kargo

Manually testing with the kargo on kind workflow is a great way to get started with Kargo development.

Additionally, Konductor and the Kargo repository are built with support for [act](https://nektosact.com/), a tool for running Github Action Runner pipelines locally. This is a great way to test your code changes for CI before committing to git.

The following commands are useful for testing Kargo CI locally:

```bash
make act
```

Running CI in GitHub Codespaces currently takes approximately 3 minutes when using the `act` tool. A successful run will conclude something like this:

![Successful act kargo on kind pipeline run](.github/images/gha-act-kargo-on-kind.png)
