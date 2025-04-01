# Kargo - Quickstart

## Getting Started

The following steps guide users through the basic steps of getting started with Kargo in [GitHub Codespaces](https://github.com/features/codespaces) or locally on a Linux machine with Docker, VSCode, and Dev Containers.

While MacOS is supported, virtual machines will not start due to the lack of nested virtualization support.

## Prerequisites

Accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)

Tools (Either/Or):

- [VSCode](https://code.visualstudio.com/download) with the [VSCode GitHub Codespaces](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces) extension.
- [Chrome](https://www.google.com/chrome) or [Edge](https://www.microsoft.com/en-us/edge) Browser to launch [GitHub Codespaces](https://github.com/features/codespaces).

#### BEFORE YOU BEGIN:

Select from the following four ways to run the quickstart:

<details><summary>Using a Web Browser</summary>

---

Tested in Google Chrome & Microsoft Edge browsers.

| Step Number | Action                                                                                       | Example / Suggestions          |
| ----------- | -------------------------------------------------------------------------------------------- | ------------------------------ |
| 1           | Open the [Kargo GitHub repository](https://github.com/ContainerCraft/Kargo) in your browser. |                                |
| 2           | Click the `Code` button and select the `Codespaces` tab.                                     |                                |
| 3           | Click `Codespaces > New with options` in the 3-dot menu.                                     |                                |
| 4           | Select the following options:                                                                |                                |
|             | __Branch__                                                                                   | `main`                         |
|             | __Dev container configuration__                                                              | `konductor`                    |
|             | __Region__                                                                                   | `$USERS_CHOICE`                |
|             | __Machine type__                                                                             | `4 cores, 16 GB RAM` or better |
| 5           | Click the `Create` button.                                                                   |                                |

Wait for the Codespace to build, then continue with the [How To](#how-to) instructions.

---

</details>

<details><summary>Using VSCode with GitHub Codespaces</summary>

---

Run the following steps in the [VSCode command palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) by pressing `Ctrl + Shift + P`:

| Step Number | Action                                                       | Example / Suggestions  |
| ----------- | ------------------------------------------------------------ | ---------------------- |
| 1           | Type/Select `Codespaces: Create New Codespace`.              |                        |
| 2           | Select the repository using fuzzy search.                    | `ContainerCraft/Kargo` |
| 3           | Select the branch.                                           | `main`                 |
| 4           | Select an instance size of at least `4 cores & 16GB of RAM`. |                        |

Wait for the Codespace to build, then continue with the [How To](#how-to) instructions.

</details>

<details><summary>Using VSCode with Docker + Dev Containers on Local Linux Machine</summary>

Ensure you have the following installed:

[![Kargo Kubevirt PaaS IaC Quickstart Prerequisites on Linux](https://img.youtube.com/vi/RyXZrcZKen8/0.jpg)](https://www.youtube.com/watch?v=RyXZrcZKen8)

- [Docker](https://docs.docker.com/get-docker/)
- [VSCode](https://code.visualstudio.com/download)
- [VSCode Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

| Step | Action                                                                                                        | Example / Suggestions                               |
| ---- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 1    | Launch [VSCode command palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) | Key combo: `Ctrl + Shift + P`                       |
| 2    | Type/Select                                                                                                   | `Dev Containers: Clone Repository in Named Volume`. |
| 3    | Type in fuzzy search for the git repository.                                                                  | `ContainerCraft/Kargo`                              |
| 4    | Enter a name for the container volume.                                                                        | `vsc-remote-containers-kargo`                       |
| 5    | Enter the cloned destination folder name.                                                                     | `Kargo` (default recommended)                       |

Wait for the dev container to build and open in VSCode, then proceed with [How To](#how-to) instructions.

---

</details>

<details><summary>Using VSCode with Docker + Dev Containers on Local MacOS Machine</summary>

---

**NOTE:** This works for platform development. Kubevirt VMs will not start due to missing nested virtualization features.

Ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [VSCode](https://code.visualstudio.com/download)
- [VSCode Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

| Step | Action                                                                                                        | Example / Suggestions                               |
| ---- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 1    | Launch [VSCode command palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) | Key combo: `Ctrl + Shift + P`                       |
| 2    | Type/Select                                                                                                   | `Dev Containers: Clone Repository in Named Volume`. |
| 3    | Type in fuzzy search for the git repository.                                                                  | `ContainerCraft/Kargo`                              |
| 4    | Enter a name for the container volume.                                                                        | `vsc-remote-containers-kargo`                       |
| 5    | Enter the cloned destination folder name.                                                                     | `Kargo` (default recommended)                       |

Wait for the dev container to build and open in VSCode, then proceed with [How To](#how-to) instructions.

---

</details>

## How To

[![Deploy Kargo Kubevirt PaaS IaC Quickstart on Linux](https://img.youtube.com/vi/qo7EfF-xdK0/0.jpg)](https://www.youtube.com/watch?v=qo7EfF-xdK0)

1. Open the [VSCode integrated terminal](https://code.visualstudio.com/docs/editor/integrated-terminal) by pressing '`Ctrl + ``'.
2. Login to Pulumi Cloud by running `pulumi login` in the terminal.

```sh
pulumi login
```

3. Launch Talos-in-Docker Kubernetes + Deploy Kargo Kubevirt PaaS IaC.

```sh
task configure
task kubernetes
```

```sh
task deploy
```

4. Deploy a new Kubevirt VM instance

```bash
# Enable the VM instance
pulumi config set --path vm.enabled true

# Deploy the Kubevirt VM instance
pulumi up
```

5. SSH to the new Ubuntu VM instance

```bash
# Access the VM instance via ssh
ssh -p 30590 -i ~/.ssh/id_rsa kc2@localhost screenfetch
```

6. Practice using the `virtctl` command to access the VM instance.

```bash
# Access the VM instance via ssh with virtctl
# uname:passwd = kc2:kc2
virtctl ssh kc2@ubuntu

# Access the VM instance via serial console
virtctl console ubuntu
```

> **NOTE:** `virtctl console` connects serial console. To exit the console, press `Ctrl + ]` or delete the integrated terminal.

6. Cleanup

```bash
task clean
```

### Developing Kargo

Manually testing with the kargo on kind workflow is a great way to get started with Kargo development.

Additionally, Konductor and the Kargo repository are built with support for [act](https://nektosact.com/), a tool for running Github Action Runner pipelines locally. This is a great way to test your code changes for CI before committing to git.

The following commands are useful for testing Kargo CI locally:

```bash
task act
```
