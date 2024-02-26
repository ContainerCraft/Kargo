# Kargo Platform Development Pathfinding Journal

## Turing Pi 2 + 4x RK1 32GB Kubevirt Cluster

In this gist we will attempt to capture the prominent steps in building an RK1 TPI2 Talos K8s Cluster for use with the github.com/ContainerCraft/Kargo kubevirt platform.

## Info

If you try this and achieve success imaging your RK1 compute modules with the un-merged talos rk1 fork please report your success on this rfe issue: [github.com/siderolabs/talos/issues/8187](https://github.com/siderolabs/talos/issues/8187)

## Update Turing Pi 2 BMC Firmware

- https://docs.turingpi.com/docs/turing-pi2-bmc-v1x-to-v2x

```bash
# download latest turingpi firmware
# - source: https://firmware.turingpi.com/turing-pi2
curl -LO https://firmware.turingpi.com/turing-pi2/v2.0.5/tp2-firmware-sdcard-v2.0.5.img

# Write firmware to microsd card
# - this command works on mac and linux
# - replace your firmware file name and disk path with your actual file and disk
# - use extreme caution this command can cause permanent data loss, mistakes can be costly
sudo dd if=tp2-firmware-sdcard-v2.0.5.img of=/dev/disk6 conv=sync bs=32k status=progress

# Insert microsd card on bottom of Turing Pi 2 board & power on
# Press the power button 3x after you observe all nic led lights solid on indicating it is ready to flash
# Node will auto reboot

# SSH to BMC
# root:turing
ssh root@192.168.1.172

# Open BMC WebUI
# root:turing
https://192.168.1.172/

# symlink sdcard storage
ln -s /mnt/sdcard ~
```

## Flash Talos images to RK1 Compute Modules

- ssh to tpi2 bmc
- cd to your sdcard storage

```bash
# download talos metal rk1 arm64 image
# - source: https://github.com/nberlee/talos/releases
curl -LOk https://github.com/nberlee/talos/releases/download/v1.6.5/metal-turing_rk1-arm64.raw.xz

# Extract the xz compressed image
unxz metal-turing_rk1-arm64.raw.xz

# flash the 4 rk1 nodes
tpi flash --local --image-path /mnt/sdcard/img/metal-turing_rk1-arm64.raw --node 1
tpi flash --local --image-path /mnt/sdcard/img/metal-turing_rk1-arm64.raw --node 2
tpi flash --local --image-path /mnt/sdcard/img/metal-turing_rk1-arm64.raw --node 3
tpi flash --local --image-path /mnt/sdcard/img/metal-turing_rk1-arm64.raw --node 4
```

## Boot all 4 nodes

```bash
tpi power on --node 1
tpi power on --node 2
tpi power on --node 3
tpi power on --node 4
```

## Coffee break

Give these nodes a couple minutes to start up so you can collect the entire uart log output in one command. This is a great time to get a beverage, check on people and pets, and the RK1s will be ready for the next step when you get back :)

## Pull serial uart console to find each node's IP address

```bash
tpi uart --node 1 get | tee /mnt/sdcard/uart.1.log | grep "assigned address"
tpi uart --node 2 get | tee /mnt/sdcard/uart.2.log | grep "assigned address"
tpi uart --node 3 get | tee /mnt/sdcard/uart.3.log | grep "assigned address"
tpi uart --node 4 get | tee /mnt/sdcard/uart.4.log | grep "assigned address"
```

<img width="837" alt="image" src="https://gist.github.com/assets/54747391/62874818-7d65-47ea-8d5c-db6be8536023">

It looks like I have the following DHCP assigned IP addresses

- 192.168.1.172 [BMC]
- 192.168.1.186
- 192.168.1.199
- 192.168.1.175
- 192.168.1.174

## Now you're ready to cluster your Talos nodes!

> Note: All following commands are run from the git repository opened in VSCode Konductor Devcontainer
> \*unless otherwise specified

### 1. Generate Talos Cluster Configuration File(s)

> Note: Talos Kubernetes Version Support Matrix Link: https://www.talos.dev/latest/introduction/support-matrix

```bash
# Prepare the local directory
mkdir -p .kube .talos
direnv allow

# Check hardware components
# Find the IP Address of your node on the talos console top right information list

# Query the network links of your node(s) and save the output to a yaml file
talosctl --nodes 192.168.1.186 get links -o yaml --insecure | tee 51.links.list
talosctl --nodes 192.168.1.199 get links -o yaml --insecure | tee 52.links.list
talosctl --nodes 192.168.1.175 get links -o yaml --insecure | tee 53.links.list
talosctl --nodes 192.168.1.174 get links -o yaml --insecure | tee 54.links.list

# Find the disk configuration of your node(s)
talosctl --nodes 192.168.1.186 disks --insecure | tee 51.disks.list
talosctl --nodes 192.168.1.199 disks --insecure | tee 52.disks.list
talosctl --nodes 192.168.1.175 disks --insecure | tee 53.disks.list
talosctl --nodes 192.168.1.174 disks --insecure | tee 54.disks.list

# Generate your talos kubernetes secrets
talosctl gen secrets --output-file secrets.yaml

# Generate the talos machine boilerplate configuration files
# Populate the install disk flag with the block device of your choice following the disks.list from earlier
talosctl gen config kargo "https://api.turing.kargo.dev:6443" \
    --additional-sans "192.168.1.50,192.168.1.51,192.168.1.52,192.168.1.53,api.turing.kargo.dev" \
    --with-secrets ./secrets.yaml \
    --kubernetes-version "1.29.0" \
    --talos-version "v1.6.3" \
    --install-disk /dev/mmcblk0 \
    --persist \
    --output .
```

### 4. Edit Talos Machine Configuration File(s)

- Validate the talos machine configuration file(s) with the following command
- Resolve any errors before proceeding

```bash
talosctl validate --mode metal --config 51.controlplane.yaml
talosctl validate --mode metal --config 52.worker.yaml
talosctl validate --mode metal --config 53.worker.yaml
talosctl validate --mode metal --config 54.worker.yaml
```

> see included pathfinder/41.controlplane.yaml for example

### 5. Apply Talos Cluster Config

```bash
# Apply the cluster configuration to each node
talosctl apply-config \
    --nodes 192.168.1.186 \
    --endpoints 192.168.1.186 \
    --file 51.controlplane.yaml \
    --insecure

# Bootstrap the first controlplane etcd node
# *be careful to wait for node to cycle through reboot before proceeding to bootstrap command
# *bootstrap may return an error if the node is not ready after the network bridge creation config applies
talosctl bootstrap \
    --nodes 192.168.1.51 \
    --endpoints 192.168.1.51

# Apply configuration to remaining worker nodes
talosctl apply-config \
    --nodes 192.168.1.199 \
    --endpoints 192.168.1.199 \
    --file 54.worker.yaml \
    --insecure

talosctl apply-config \
    --nodes 192.168.1.175 \
    --endpoints 192.168.1.175 \
    --file 55.worker.yaml \
    --insecure

talosctl apply-config \
    --nodes 192.168.1.174 \
    --endpoints 192.168.1.174 \
    --file 56.worker.yaml \
    --insecure
```

### 6. Load configs in local directory tree for now

```bash
# move talosconfig to .talos/config
mv talosconfig .talos/config

# My talos config generated an endpoint address of 127.0.0.1
# this obviously will not work so let's change that to our VIP
sed -i 's/127.0.0.1/192.168.1.50/g' .talos/config

# Generate kubeconfig ./.kube/config
talosctl --nodes 192.168.1.51 kubeconfig .kube/config --force

# Kubeconfig is generated with FQDN API endpoint by default since I configured it in the machine cfg
# If DNS is not configured to resolved your api endpoint you can use the following command to replace the FQDN with the IP Address
# Use the IP Address of the VIP for your controlplane in place of the DNS name of your endpoint
sed -i 's/api.kube.kargo.dev/192.168.1.50/g' .kube/config
```

### 7. Check your cluster status

```bash
# Check the status of your cluster
kubectl get po -A

# check for pending Certificate Signing Requests (CSR)
kubectl get csr

# Approve the pending CSR(s)
kubectl get csr | awk '/Pending/ {print $1}' | xargs -n 1 kubectl certificate approve

# Check the status of your cluster
# All pods should come up except for coredns pods because we still need to deploy the cilium CNI
kubectl get po -A
```

![screenshot of bootstrapping talos cluster with controlplane configs and etcd bootstrap command](.assets/02-vscode-talosctl-apply-config.png)

## References

```bash
# Get Talos Disk Usage
talosctl --nodes 192.168.1.51 usage -H 2>/dev/null | grep -v readlink | tee du.list
```

### Apply Config Changes

```bash
# Apply the cluster configuration to each node
talosctl apply-config \
    --nodes 192.168.1.51 \
    --endpoints 192.168.1.51 \
    --file 51.controlplane.yaml

talosctl apply-config \
    --nodes 192.168.1.52 \
    --endpoints 192.168.1.52 \
    --file 52.worker.yaml

talosctl apply-config \
    --nodes 192.168.1.53 \
    --endpoints 192.168.1.53 \
    --file 53.worker.yaml

talosctl apply-config \
    --nodes 192.168.1.54 \
    --endpoints 192.168.1.54 \
    --file 53.worker.yaml
```

### Wipe Nodes & Reset

```bash
# If necessary perform an API call to reset the node(s) to a clean state
# CAUTION:
#  - This will destroy all data on the node(s)

talosctl reset --debug \
    --nodes 192.168.1.51 \
    --endpoints 192.168.1.51 \
    --system-labels-to-wipe STATE \
    --system-labels-to-wipe EPHEMERAL \
    --graceful=false \
    --reboot

talosctl reset --debug \
    --nodes 192.168.1.52 \
    --endpoints 192.168.1.52 \
    --system-labels-to-wipe STATE \
    --system-labels-to-wipe EPHEMERAL \
    --graceful=false \
    --reboot

talosctl reset --debug \
    --nodes 192.168.1.53 \
    --endpoints 192.168.1.53 \
    --system-labels-to-wipe STATE \
    --system-labels-to-wipe EPHEMERAL \
    --graceful=false \
    --reboot

talosctl reset --debug \
    --nodes 192.168.1.54 \
    --endpoints 192.168.1.54 \
    --system-labels-to-wipe STATE \
    --system-labels-to-wipe EPHEMERAL \
    --graceful=false \
    --reboot
```
