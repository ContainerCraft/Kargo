# Konductor DevOps Userspace Container

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ContainerCraft/konductor)

Konductor is a DevOps practitioner userspace container.

Available in two forms:

1. [Devcontainer](https://containers.dev/) for use with [VSCode](https://code.visualstudio.com/docs/devcontainers/containers) and [Codespaces](https://docs.github.com/en/codespaces/overview)
1. [VSCode Code Server](https://code.visualstudio.com/blogs/2022/07/07/vscode-server) selfhosted VSCode cloud developer IDE

![Konductor](./.github/images/konductor.png)

## About

Included:
- [Fish Shell](https://fishshell.com)
- [Starship prompt by starship.rs](https://starship.rs)
- [VS Code Server by coder.com](https://coder.com/docs/code-server/latest)
- [TTYd Terminal Server](https://github.com/tsl0922/ttyd)
- [SSH Server](https://www.ssh.com/academy/ssh/server)
- [SSH](https://www.ssh.com/academy/ssh/openssh)
- [Tmux](https://github.com/tmux/tmux/wiki/Getting-Started)
- [Tmate](https://tmate.io)
- [Helm](https://helm.sh/docs/)
- [K9s](https://k9scli.io)
- [Kubectl](https://kubernetes.io/docs/reference/kubectl/)
- [VirtCtl](https://kubevirt.io/user-guide/operations/virtctl_client_tool/)
- [Pulumi](https://www.pulumi.com/docs/get-started/)
- [Talosctl](https://www.talos.dev/v1.2/reference/cli/)
- [Jq](https://stedolan.github.io/jq/)
- [Yq](https://github.com/mikefarah/yq)

## Getting Started

There are 3 ways to get started:

1. Add to your own project as a [Git Submodule](#git-submodule)
1. [Open in GitHub Codespaces](https://codespaces.new/ContainerCraft/konductor)
1. VSCode Devcontainer

### Git Submodule

The Konductor Devcontainer repository can be added as a submodule to your own projects to provide an easy and consistent development environment.

To add this repository as a submodule to your project, run the following commands:

```bash
git submodule add https://github.com/containercraft/konductor .devcontainer
git submodule update --init --recursive .devcontainer
```

To update the devcontainer submodule in consuming repos:

```bash
git submodule update --remote --merge .devcontainer
```

After the submodule is added, you can open your project in VS Code and it will automatically detect the Dev Container configuration and prompt you to open the project in a container, or you can open the project in Github CodeSpaces.

To remove the devcontainer submodule:

```bash
git rm -r .devcontainer
git rm .devcontainer.json
rm -rf .git/modules/.devcontainer
git config --remove-section submodule..devcontainer
```

### GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ContainerCraft/konductor)

> (Click to open)

### VSCode Devcontainer

Learn more about how to use Devcontainers with VSCode: ([LINK](https://learn.microsoft.com/en-us/training/modules/use-docker-container-dev-env-vs-code/))
