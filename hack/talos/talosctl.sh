#!/bin/bash -x
#talosctl gen secrets
talosctl gen config dev https://192.168.1.60:6443/ \
--install-image "factory.talos.dev/installer/d1cba4b30888a004f2da2ec088afa62af8bf97b049367afec139490bec401a73:v1.7.2" \
--output-types controlplane,worker,talosconfig \
--with-secrets secrets.yaml \
--config-patch @tmpl.yaml \
--install-disk "/dev/vda" \
--output ./ \
--persist \
--force

kubectl create secret generic talos-userdata-cp1 --dry-run=client --output=yaml \
--from-file=userdata=controlplane.yaml \
| kubectl apply -f -
