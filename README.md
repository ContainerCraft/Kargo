# Kargo Community Homelab Platform Engineering

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ContainerCraft/Kargo)

[![CI - Kargo on Kind](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml/badge.svg)](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml)

Join the conversation on the [ContainerCraft Community Discord Kargo Channel](https://discord.gg/BAMwwqys).

> NOTE: This project is in pre-alpha pathfinding mode. See the [inaugural Twitter/X Thread post](https://x.com/usrbinkat/status/1749186949590794551) by [@usrbinkat](https://twitter.com/usrbinkat)
>
> Kargo Project opened in the [Konductor Devcontainer](https://github.com/ContainerCraft/Konductor) with Github Codespaces.
> ![Screenshot of Kargo open in Konductor Devcontainer](.github/images/konductor-codespaces.png?raw=true "Kargo Konductor Codespaces")

## About

Kargo is a community project to build the first Platform Engineered Homelab for the ContainerCraft community. The project is a collaboration between the ContainerCraft community and the Kubernetes industry leaders and practitioners to build a common sharable platform for learning, experimentation, and collaboration.

For more information, see the [Kargo Project FAQ](FAQ.md).

## Goals

* Eliminate the barrier to entry for learning Kubernetes and Cloud Native technologies
* Provide a common platform for the community to collaborate and share knowledge
* Enable anyone to experience the power of owning a local cloud platform
* Accelerate the time-to-achievement for new projects and ideas
* Invest in a common library of reusable middleware and application IaC for Kargo
* Select enterprise grade technologies and practices to build a valuable learning platform
* Be the best hypervisor and container platform for the Homelab community

## Non-Goals

* Kargo is not a production platform
* Kargo will not try to be everything for everyone

## Getting Started

### Prerequisites

Success with Kargo depends on two things, the server side infrastructure, and the client side tooling.

Kargo is the server side platform, and the client side tooling is distributed via the [ContainerCraft Konductor](https://github.com/ContainerCraft/Konductor) devcontainer.

#### Client Side Cloud Dependencies

If running in Github Codespaces, all you need is a browser and a Github account!

#### Client Side Local Dependencies

If running locally on your own machine, you will need the following:

* [Visual Studio Code](https://code.visualstudio.com/)
* [Visual Studio Code Remote - Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
* [Docker Desktop](https://www.docker.com/products/docker-desktop)

#### Server Side Dependencies

There are two ways to run the server side infrastructure for Kargo. Choose between running, testing, and developing Kargo using [Kind](https://kind.sigs.k8s.io/) from within the Konductor container, or running Kargo on a local or remote [Sidero Talos Kubernetes](https://talos.dev/) cluster.

##### Virtual Kind Kubernetes

Using Kind is the easiest way to get started with Kargo. Kind is a Kubernetes-in-Docker platform that allows you to run a Kubernetes cluster on your local machine. Kind allows for easy testing and development of Kubernetes and Kargo and is the recommended first step for new Kargonauts to familiarize yourself with the project before investing in and provisioning physical hardware.

Kind is also used by the Kargo maintainers and contributors to develop and test Kargo.

##### Physical Talos Kubernetes

[Talos](https://talos.dev/) is a modern OS for Kubernetes. Talos is designed to be secure, immutable, and minimal. Talos is the recommended platform for running Kargo in a production-like homelab environment. Find out more about why in our [FAQ](FAQ.md).

### How to Run Kargo on Kind

> NOTE: the following assumes you have already installed VSCode, the Remote Containers extension, and Docker Desktop.

1. Clone the Kargo repository to your local machine
2. Open the Kargo repository in VSCode
3. When prompted, click "Reopen in Container" to open the Kargo repository in the Konductor devcontainer
4. Once the devcontainer is open, run the following command to start Kargo on Kind:

```bash
make kind-up
```

5. Once the Kind cluster is running, you can validate access the Kubernetes API with the following command:

```bash
kubectl cluster-info
```

6. Deploy the Kargo platform to the Kind cluster with the following commands:

> NOTE: substitute your kubecontext name for `kind-kargo` if you are using a different kubecontext.

```bash
# Setup Pulumi CLI
pulumi login
pulumi install
pulumi stack select --create kind-kargo

# Configure & Deploy Kargo
pulumi config set kubernetes kind
pulumi config set kubecontext kind-kargo
pulumi up
```
