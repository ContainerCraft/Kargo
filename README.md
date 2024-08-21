---
cwd: /workspaces/Kargo
shell: /usr/bin/bash
---

# Kargo - The Cloud-Native ESXi Replacement

[![CI - Kargo on Kind](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml/badge.svg)](https://github.com/ContainerCraft/Kargo/actions/workflows/kind.yaml)

## About

Join the conversation on the [ContainerCraft Community Discord Kargo Channel](https://discord.gg/Jb5jgDCksX).

Kargo is a community project to build the first Platform Engineered virtualization environment to replace the need for hypervisors that may no longer be suitable for cloud-native environments. The project is a collaboration between the ContainerCraft community, Kubernetes industry leaders, virtualization experts, and practitioners to build a common sharable platform for virtualized environments in both on-prem, cloud, and local environments.

For more information, see the [Kargo Project FAQ](FAQ.md).

![Screenshot of the Kargo project opened in the Konductor Devcontainer with Github Codespaces.](.github/images/konductor-docker-linux-devcontainer.png?raw=true "Kargo Konductor Codespaces")

> \*Image depicts Kargo Project opened in the [Konductor Devcontainer](https://github.com/ContainerCraft/Konductor) with Github Codespaces.
>
> **NOTE**: This project is in pre-alpha pathfinding mode. See the [inaugural Twitter/X Thread post](https://x.com/usrbinkat/status/1749186949590794551) by [@usrbinkat](https://twitter.com/usrbinkat)

### Goals

- Simpler Kubernetes skills development
- Accelerate time-to-success for new projects and ideas
- Build a common community platform for sharing and collaboration
- Build an enterprise-grade hyperconverged homelab compute platform
- Develop a reliable platform for community equity building

## Getting Started

The following steps guide users through the basic steps of getting started with Kargo in [GitHub Codespaces](https://github.com/features/codespaces) or locally on a Linux machine with Docker, VSCode, and Dev Containers.

While MacOS is supported, virtual machines will not start due to the lack of nested virtualization support.

## Prerequisites

Tools and Accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)
3. [Chrome](https://www.google.com/chrome) or [Edge](https://www.microsoft.com/en-us/edge) Browser

## How To

[![Deploy Kargo Kubevirt PaaS IaC Quickstart on Linux](https://img.youtube.com/vi/qo7EfF-xdK0/0.jpg)](https://www.youtube.com/watch?v=qo7EfF-xdK0)

---

1. Login to Github
2. Launch [Kargo in Github Codspaces](https://bit.ly/launch-kargo-kubevirt-paas-in-github-codespaces)

> 
>
> <details><summary> > Click to expand < </summary>
>
> > _Find other ways to run the quickstart in the [Kargo Quickstart Guide](docs/QUICKSTART.md)._
>
> Using either [Google Chrome](https://www.google.com/chrome) or [Microsoft Edge](https://www.microsoft.com/en-us/edge), follow the steps below to launch the Kargo project in GitHub Codespaces from your browser.
>
> | Step Number | Action                                                                                       | Example / Suggestions          |
> | ----------- | -------------------------------------------------------------------------------------------- | ------------------------------ |
> | 1           | Open the [Kargo GitHub repository](https://github.com/ContainerCraft/Kargo) in your browser. |                                |
> | 2           | Click the `Code` button and select the `Codespaces` tab.                                     |                                |
> | 3           | Click `Codespaces > New with options` in the 3-dot menu.                                     |                                |
> | 4           | Select the following options:                                                                |                                |
> |             | __Branch__                                                                                   | `main`                         |
> |             | __Dev container configuration__                                                              | `konductor`                    |
> |             | __Region__                                                                                   | `$USERS_CHOICE`                |
> |             | __Machine type__                                                                             | `4 cores, 16 GB RAM` or better |
> | 5           | Click the `Create` button.                                                                   |                                |
>
> Wait for the Codespace to build, and then proceed.
>
> </details>

3. Open the [VSCode integrated terminal](https://code.visualstudio.com/docs/editor/integrated-terminal) by pressing `[ Ctrl + ` ]`.
4. Login to Pulumi Cloud by running `pulumi login` in the terminal.

```sh {"id":"01J5PTD6JZYE6F79ZEAEG8FY41","name":"step4-login-task","terminalRows":"25"}
pulumi login
```

```sh {"id":"01J5S0W4CQ3XSZXR5N449SPNE9","name":"task0-printenv-test","terminalRows":"20"}
echo $PWD
env | grep -iE "PWD|HOME"
```

```sh {"id":"01J5TZA82C9S924N36FVQS9BRH"}
/usr/bin/echo $PWD
/usr/bin/echo $KUBECONFIG
/usr/bin/task printenv
```

5. Launch Talos-in-Docker Kubernetes + Deploy Kargo Kubevirt PaaS IaC.

```sh {"id":"01J5PTD6JZYE6F79ZEAJ5XWTPG","name":"step5-deploy-task","terminalRows":"40"}
task talos
```

```sh {"cwd":"/workspaces/Kargo","id":"01J5V1EC07VNW61SKJTK7AEPDR","terminalRows":"40"}
set -x
cat $KUBECONFIG
echo $KUBECONFIG
echo $PWD
ls -lah
ls -lah .pulumi
which pulumi
pulumi up --verbose 9
```

6. Deploy a new Kubevirt VM instance

```bash {"id":"01J5PTD6JZYE6F79ZEAKYKZ1D9","name":"step6-deploy-vm"}
# Enable the VM instance
pulumi config set --path vm.enabled true

# Deploy the Kubevirt VM instance
pulumi up
```

7. SSH to the new Ubuntu VM instance (ignore strict host key checking).

```bash {"id":"01J5PTD6JZYE6F79ZEAN9XGXBQ","name":"step7-access-vm"}
# Access the VM instance via ssh
ssh -p 30590 -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no kc2@localhost screenfetch
```

8. Practice using the `virtctl` command to access the VM instance.

```bash {"id":"01J5PZ5GDMMFDRGG3D5G0ZGDBV","name":"step8-virtctl"}
# Access the VM instance via ssh with virtctl
# uname:passwd = kc2:kc2
virtctl ssh kc2@ubuntu
```

```bash {"id":"01J5Q78V4RYNTPDDA9ASXTGSR1","name":"step9-virtctl"}
# Access the VM instance via serial console
virtctl console ubuntu
```

> **NOTE:** `virtctl console` connects serial console. To exit the console, press `Ctrl + ]` or delete the integrated terminal.

10. Cleanup

```bash {"id":"01J5PTD6JZYE6F79ZEANMY688P","name":"step10-cleanup"}
task clean
```

## Contributing

Kargo is a community project and we welcome contributions from everyone. Please see [CONTRIBUTING.md](https://github.com/ContainerCraft/Kargo/issues/22) for more information on how to get involved.

To get started, join the conversation on the [ContainerCraft Community Discord Kargo Channel](https://discord.gg/Jb5jgDCksX).

### Developing Kargo

Manually testing with the kargo on kind workflow is a great way to get started with Kargo development.

Additionally, Konductor and the Kargo repository are built with support for [act](https://nektosact.com/), a tool for running Github Action Runner pipelines locally. This is a great way to test your code changes for CI before committing to git.

The following commands are useful for testing Kargo CI locally:

```bash {"id":"01J5PTD6JZYE6F79ZEAP4QGVMA","name":"test-kargo-ci"}
task act
```
