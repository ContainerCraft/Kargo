#!/bin/bash -ex
export ARCH="$(uname -m | awk '{ if ($1 == "x86_64") print "amd64"; else if ($1 == "aarch64" || $1 == "arm64") print "arm64"; else print "unknown" }')" \

#rm -rf .talos/{state,manifest}
#mkdir -p .talos/{state,manifest}
#
#talosctl gen config kargo https://127.0.0.1:6443 \
#    --config-patch @.talos/patch/machine.yaml \
#    --kubernetes-version "1.29.0" \
#    --output .talos/manifest \
#    --with-examples=false \
#    --with-docs=false \
#;echo

talosctl cluster create \
    --arch="$ARCH" \
    --cpus 2 \
    --workers 1 \
    --controlplanes 1 \
    --provisioner docker \
    --docker-disable-ipv6 \
    --state .talos/state \
    --wait-timeout="20m0s" \
    --docker-host-ip "0.0.0.0" \
    --input-dir .talos/manifest \
    --exposed-ports="80:8080/tcp,443:8443/tcp,7445:7445/tcp" \
    --wait=true \
;echo

#   --disk 6144 \
#   --user-disk="/var/mnt/local-path-provisioner/dev/ssd:6144" \
#   --extra-disks 1 \
#   --extra-disks-size 5120 \
#   --with-debug                               enable debug in Talos config to send service logs to the console
#   --config-patch stringArray                 patch generated machineconfigs (applied to all node types), use @file to read a patch from file
#   --init-node-as-endpoint                    use init node as endpoint instead of any load balancer endpoint
#   --kubernetes-version string                desired kubernetes version to run (default "1.29.0")
#   --memory int                               the limit on memory usage in MB (each control plane/VM) (default 2048)
#   --memory-workers int                       the limit on memory usage in MB (each worker/VM) (default 2048)
#   --registry-mirror strings                  list of registry mirrors to use in format: <registry host>=<mirror URL>
#   --use-vip                                  use a virtual IP for the controlplane endpoint instead of the loadbalancer

#   --config-patch-control-plane stringArray   patch generated machineconfigs (applied to 'init' and 'controlplane' types)
#   --config-patch-worker stringArray          patch generated machineconfigs (applied to 'worker' type)

#   --registry-mirror strings   list of registry mirrors to use in format: <registry host>=<mirror URL>
#   --cluster string            Cluster to connect to if a proxy endpoint is used.
#   --context string            Context to be used in command
#   --endpoints strings         override default endpoints in Talos configuration
#   --force                     will overwrite existing files
#   --nodes strings             target the specified nodes
#   --talosconfig string        The path to the Talos configuration file. Defaults to 'TALOSCONFIG' env variable if set, otherwise '$HOME/.talos/config' and '/var/run/secrets/talos.dev/config' in order.
