# Using iSCSI

iSCSI is a popular way to provide remote storage using TCP/IP.  This doc won't get into the details as to how iSCSI works, other then how it is integrated with Talos Linux.  These instructions are based off of integrating a Synology NAS into Talos using the Synology Container Storage Interface (CSI) driver, which allows a Talos cluster to dynamically provision iSCSI volumes for `StatefulSets` and other workloads.

## Enabling iSCSI

Talos is a container first Linux distro built to run Kubernetes.  Unlike Ubuntu, RHEL, Debian, and other general-purpose Linux distributions, Talos doesn't have a package manager where you can install binaries.  Everything has to be provided either as an image or an extension.  So where you may login to an Ubuntu box and run `apt install` to get the correct packages, that isn't an option with Talos.  The iSCSI capabilities in Talos are provided as an extension that must be provided in the image used.  The easiest way to generate the correct image is to use Talos' image factory.

Go to https://factory.talos.dev/ and choose your version and check the box next to `siderolabs/iscsi-tools (v...)` and click ***Submit***.  This will generate a list of potential image sources.  The one you use will be based on if you're updating an existing install or starting a new one.

### New Installs

Download the iso or PXE Boot image that works best for you and run your installation.

### Upgrades

Copy the `Installer Image`, which is a docker container.  Then, for each node, run:


*For each node in a multi-node cluster:*

```
talosctl upgrade --nodes 192.168.2.231 --image factory.talos.dev/installer/ffdc59f4fd5b62784876a03c3e31a81fbfecc871eaa7f27aca33b9f5ff1ec96e:v1.6.7 
```

*In a single node cluster:*

```
talosctl upgrade --nodes 192.168.2.231 --image factory.talos.dev/installer/ffdc59f4fd5b62784876a03c3e31a81fbfecc871eaa7f27aca33b9f5ff1ec96e:v1.6.7  --preserve=true
```

With a single node cluster `--preserve=true` makes sure that the cluster's config and data are preserved.

### Validation

Once the upgrade is completed, you can verify that iSCSI is running by first checking for the extension:

```
talosctl get extensions --nodes 192.168.2.231                                                                                                                  
NODE            NAMESPACE   TYPE              ID   VERSION   NAME               VERSION
192.168.2.231   runtime     ExtensionStatus   0    1         iscsi-tools        v0.1.4
```

And that the `ext-iscsi` service is running:

```
talosctl services --nodes 192.168.2.231                         
NODE            SERVICE      STATE     HEALTH   LAST CHANGE   LAST EVENT
192.168.2.231   apid         Running   OK       41m11s ago    Health check successful
192.168.2.231   containerd   Running   OK       42m10s ago    Health check successful
192.168.2.231   cri          Running   OK       41m9s ago     Health check successful
192.168.2.231   dashboard    Running   ?        42m3s ago     Process Process(["/sbin/dashboard"]) started with PID 2771
192.168.2.231   etcd         Running   OK       41m4s ago     Health check successful
192.168.2.231   ext-iscsid   Running   ?        41m7s ago     Started task ext-iscsid (PID 3320) for container ext-iscsid
.
.
.
```

Now, you can update your CSI implementation.

## Using the ext-iscsi Service

In order to use iSCSI, you need to have your CSI implementation enter the `ext-iscsi` service to run the `iscsiadmin` binary.  Since CSIs run as containers, it means your CSI `Pod`s needs to run with the `spec.hostPID` flag as `true` so your implementation can first find, then enter the `ext-iscsi` service on each node.

CSIs are generally implemented with at least one `DaemonSet` so they can mount the remote volume onto the node that the container that attaches to it will run on.  This means that the `DaemonSet` must have `spec.template.spec.hostPID` set to true.  This will allow the CSI to access the `ext-iscsi` service.  In addition to updating the `DaemonSet`, you'll need to update your CSI to to enter the process.  If your CSI mounts a `ConfigMap` with the script, that makes it easier.  Otherwise you'll need to update your container.  For the synology CSI, the update was to the `chroot/chroot.sh` file.  The original file attempts to locate the `iscsiadmin` binary using `env`.  Unfortunately, `env` is not available in Talos, because there aren't any shells!  Here's the original file:

```
#!/usr/bin/env bash
# This script is only used in the container, see Dockerfile.

DIR="/host" # csi-node mount / of the node to /host in the container
BIN="$(basename "$0")"

if [ -d "$DIR" ]; then
    exec chroot $DIR /usr/bin/env -i PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" "$BIN" "$@"
fi

echo -n "Couldn't find hostPath: $DIR in the CSI container"
exit 1
```

here is the updated version:

```
#!/usr/bin/env bash
# This script is only used in the container, see Dockerfile.

DIR="/host" # csi-node mount / of the node to /host in the container
BIN="$(basename "$0")"

iscsid_pid=$(pgrep iscsid)

echo "$@"

if [ -d "$DIR" ]; then
    echo "entering nsenter"
    nsenter --mount="/proc/${iscsid_pid}/ns/mnt" --net="/proc/${iscsid_pid}/ns/net" -- "/usr/local/sbin/$BIN" "$@"
fi

#echo -n "Couldn't find hostPath: $DIR in the CSI container /usr/local/sbin/$BIN $@"
#exit 1
```

The first change is to find the `ext-iscsi` process id: `iscsid_pid=$(pgrep iscsid)` - this tells us which process to enter.  Then, we use `nsenter` to enter the `ext-iscsi` process so we can run `iscsiadmin`.  We also removed `exec` and hard coded the path because there's no shell!: `nsenter --mount="/proc/${iscsid_pid}/ns/mnt" --net="/proc/${iscsid_pid}/ns/net" -- "/usr/local/sbin/$BIN" "$@"`.  Finally, we removed the `echo` and `exit` statement because no `exec` means tha the process will continue instead of being taken over by the `iscsiadmin` command.

Once your `DaemonSet` and containers/`ConfigMap`s are updated you'll be able to dynamically provision and mount iSCSI volumes!