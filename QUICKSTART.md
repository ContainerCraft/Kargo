# Quickstart

The following steps guide users through the basic steps of getting started with Kargo in [GitHub Codespaces] or locally on a linux machine with Docker, VSCode, and Dev Containers.

## Prerequisites

Accounts:

1. [GitHub](https://github.com)
2. [Pulumi Cloud](https://app.pulumi.com/signup)

Tools (Either/Or):

- [VSCode](https://code.visualstudio.com/download) with the [VSCode GitHub Codespaces](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces) extension.
- [Chrome](https://www.google.com/chrome) or [Edge](https://www.microsoft.com/en-us/edge) Browser to launch [GitHub Codespaces].

### BEFORE YOU BEGIN:

Select between running this quickstart in either GitHub Codespaces from within your browser window, or running in GitHub Codespaces from within a local VSCode installation with the [VSCode GitHub Codespaces](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces) extension.

### For using a Web Browser

Tested in Google Chrome & Microsoft Edge browsers.

<details><summary>click to expand steps</summary>

1. Open the [Kargo GitHub repository](https://github.com/ContainerCraft/Kargo) in your browser.
2. Click the `Code` button and select `Codespaces` tab.
3. Click the Codespaces > Codespaces > 3-dot menu > `New with options`.
4. select the following:

| Option                        | Value                          |
| ----------------------------- | ------------------------------ |
| `Branch`                      | `main`                         |
| `Dev container configuration` | `konductor`                    |
| `Region`                      | `$USERS_CHOICE`                |
| `Machine type`                | `4 cores, 16 GB RAM` or better |

5. Click the `Create` button.

Wait for Codespace build.

</details>

### For VSCode with GitHub Codespaces

Run the following steps in the [VSCode command palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) by pressing '`Ctrl + Shift + P`'

<details><summary>click to expand steps</summary>

1. `Codespaces: Create New Codespace`
2. `Select a repository` use fuzzy search to find `ContainerCraft/Kargo`
3. `Select the branch main`
4. `Select an instance size of at least 4 cores & 16GB of RAM`

Wait for Codespace build.

</details>

### For VSCode with Docker + Dev Containers on Local Linux Machine

Ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [VSCode](https://code.visualstudio.com/download)
- [VSCode Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

<details><summary>click to expand steps</summary>

1. Open the Kargo repository in VSCode.
2. Click the green `><` icon in the bottom left corner of the VSCode window.
3. Select `Remote-Containers: Reopen in Container`.
4. Select the `konductor` dev container configuration.

</details>

## How To

1. Open the VSCode [integrated terminal](https://code.visualstudio.com/docs/editor/integrated-terminal) by pressing '`` Ctrl + ` ``'.
2. Login to Pulumi Cloud by running `pulumi login` in the terminal.

```bash
# Login to Pulumi Cloud
pulumi login
```

# Start a Talos-in-Docker Kubernetes cluster

3. Execute the following commands in the terminal

```bash
# 1. Start a Talos-in-Docker Kubernetes cluster
# 2. Deploy the Kargo Kubevirt PaaS Pulumi IaC
task deploy
```

4. Deploy a Kubevirt VM instance

```bash
# Create an ssh-pubkey kubernetes secret
k create secret generic kc2-pubkey --from-file=key1=$HOME/.ssh/id_rsa.pub --dry-run=client -oyaml | k apply -f -

# Deploy a Kubevirt VM instance
kubectl apply -f hack/ubuntu-nat.yaml
```

5. Access the VM instance

```bash
# Access the VM instance via serial console
virtctl console ubuntu-ephemeral-nat

# Access the VM instance via ssh with virtctl
# uname:passwd = kc2:kc2
virtctl ssh kc2@ubuntu-ephemeral-nat

# Access the VM instance via ssh
ssh -p 30590 -i ~/.ssh/id_rsa kc2@localhost
```

[GitHub Codespaces]: https://github.com/features/codespaces
