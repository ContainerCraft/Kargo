#!/bin/bash -x
kubectl delete -f kubevirt.vm.yaml --wait=true ; sleep 1 \
; kubectl delete -f kubevirt.vm.yaml --wait=true ; sleep 3
kubectl delete secret talos-userdata-cp1 ; sleep 1

kubectl create secret generic talos-userdata-cp1 --dry-run=client --output=yaml \
--from-file=userdata=controlplane.yaml \
| kubectl apply -f -
#--from-file=networkdata=controlplane.networkdata.yaml \

kubectl apply -f kubevirt.vm.yaml || kubectl apply -f kubevirt.vm.yaml
