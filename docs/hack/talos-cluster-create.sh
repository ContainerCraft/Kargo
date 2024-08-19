#!/bin/bash -x

export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')"

talosctl cluster create --arch ${ARCH} \
      --provisioner docker \
      --name talos-kargo-docker \
      --context talos-kargo-docker \
      --controlplanes 1 --memory 2048 \
      --workers 1 --memory-workers 2048 \
      --user-disk "/var/mnt/hostpath-provisioner:4" \
      --init-node-as-endpoint \
      ; echo

#     --extra-disks int                          number of extra disks to create for each worker VM
#     --extra-disks-size int                     default limit on disk size in MB (each VM) (default 5120)
#     --config-patch stringArray                 patch generated machineconfigs (applied to all node types), use @file to read a patch from file
#     --config-patch-control-plane stringArray   patch generated machineconfigs (applied to 'init' and 'controlplane' types)
#     --config-patch-worker stringArray          patch generated machineconfigs (applied to 'worker' type)
#     --input-dir string                         location of pre-generated config files
#     --wait                                     wait for the cluster to be ready before returning (default true)
#     --wait-timeout duration                    timeout to wait for the cluster to be ready (default 20m0s)
#     --with-debug                               enable debug in Talos config to send service logs to the console
