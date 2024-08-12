#!/bin/bash

# Delete all resources in namespace
delete_resources_in_namespace() {
  local namespace=$1
  echo "Deleting all resources in namespace: $namespace"
  kubectl api-resources --verbs=list --namespaced -o name \
    | xargs -n 1 kubectl delete --all -n "$namespace" --ignore-not-found --wait
}

# Remove finalizers and delete stuck namespace
delete_namespace() {
  local namespace=$1
  echo "Removing finalizers and deleting namespace: $namespace"
  kubectl get namespace "$namespace" -o json \
    | jq 'del(.spec.finalizers)' \
    | kubectl replace --raw "/api/v1/namespaces/$namespace/finalize" -f -
  kubectl delete namespace "$namespace"
  echo "Waiting for namespace $namespace to be deleted..."
  while kubectl get namespace "$namespace" &>/dev/null; do
    sleep 1
  done
  echo "Namespace $namespace has been deleted."
}

# Check for at least one namespace provided as argument
if [ $# -eq 0 ]; then
  echo "Usage: $0 <namespace1> <namespace2> ... <namespaceN>"
  exit 1
fi

# Loop through and delete list of namespaces
for namespace in "$@"; do
  delete_resources_in_namespace "$namespace"
  delete_namespace "$namespace"
done
