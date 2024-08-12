# --- Global Variables ---

LOWERCASE_GITHUB_REPOSITORY := $(shell echo ${GITHUB_REPOSITORY} | tr '[:upper:]' '[:lower:]')
REPO_NAME := $(shell echo ${LOWERCASE_GITHUB_REPOSITORY} | awk -F '/' '{print $$2}')
REPO_ORG := $(shell echo ${LOWERCASE_GITHUB_REPOSITORY} | awk -F '/' '{print $$1}')

PROJECT ?= $(or $(REPO_NAME),kargo)
DEPLOYMENT ?= $(or $(ENVIRONMENT),ci)

# Check if PULUMI_BACKEND_URL starts with 'file://'
ifeq ($(findstring file://,$(PULUMI_BACKEND_URL)),file://)
    ORGANIZATION = organization
    $(info ORGANIZATION: ${ORGANIZATION})
else
    ORGANIZATION = ${GITHUB_USER}
    $(info ORGANIZATION is set to ${GITHUB_USER})
endif

# Set Pulumi stack identifier to <organization>/<project>/<deployment>
PULUMI_STACK_IDENTIFIER := ${ORGANIZATION}/${PROJECT}/${DEPLOYMENT}

# Escape special characters in sensitive tokens
ESCAPED_PAT := $(shell echo "${PULUMI_ACCESS_TOKEN}" | sed -e 's/[\/&]/\\&/g')
ESCAPED_GITHUB_TOKEN := $(shell echo "${GITHUB_TOKEN}" | sed -e 's/[\/&]/\\&/g')

# Define file paths for configurations
KUBE_CONFIG_FILE := .kube/config
TALOS_CONFIG_FILE := .talos/config

# Check if PULUMI_ACCESS_TOKEN is set
ifeq ($(ESCAPED_PAT),)
$(warning PULUMI_ACCESS_TOKEN is not set)
endif

# Check if GITHUB_TOKEN is set
ifeq ($(ESCAPED_GITHUB_TOKEN),)
$(warning GITHUB_TOKEN is not set)
endif

# --- Targets ---
.PHONY: help detect-arch pulumi-login pulumi-up up talos-gen-config talos-cluster clean clean-all act konductor test-talos stop force-terminating-ns

# --- Default Command ---
all: help

# --- Help ---
# Display available commands
help:
	@echo "Available commands:"
	@echo "  help             - Display this help message."
	@echo "  login            - Authenticate with Pulumi."
	@echo "  esc ENV=foobar   - Run Pulumi ESC environment. Default: ENV='kubernetes'."
	@echo "  up               - Deploy Pulumi infrastructure."
	@echo "  pulumi-down      - Destroy deployed Pulumi infrastructure."
	@echo "  talos-cluster    - Deploy a Talos Kubernetes cluster."
	@echo "  talos-config     - Generate and validate Talos configuration."
	@echo "  talos            - Create and configure a Talos Kubernetes cluster."
	@echo "  clean            - Clean up resources."
	@echo "  clean-all        - Perform 'clean' and remove Docker volumes."
	@echo "  act              - Test GitHub Actions locally."
	@echo "  konductor        - Maintain .github/devcontainer submodule."
	@echo "  test             - Run setup tests."
	@echo "  stop             - Stop Github Codespaces."

# --- Detect Architecture ---
detect-arch:
	@echo $(shell uname -m | awk '{ if ($$1 == "x86_64") print "amd64"; else if ($$1 == "aarch64" || $$1 == "arm64") print "arm64"; else print "unknown" }')

# --- Pulumi Login ---
pulumi-login:
	@echo "Logging into Pulumi..."
	@direnv allow || true
	@PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} pulumi login \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@pulumi install || true
	@set -ex; pulumi stack select --create ${PULUMI_STACK_IDENTIFIER} || true
	@echo "Login successful."

# --- Pulumi Deployment ---
pulumi-up:
	@echo "Deploying Pulumi infrastructure..."
	@KUBECONFIG=${KUBE_CONFIG_FILE} PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		pulumi up --yes --skip-preview --refresh --continue-on-error --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@KUBECONFIG=${KUBE_CONFIG_FILE} PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		pulumi up --yes --skip-preview --refresh --continue-on-error --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@KUBECONFIG=${KUBE_CONFIG_FILE} PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		pulumi up --yes --skip-preview --refresh --continue-on-error --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g'
	@echo "Deployment complete."

pulumi-down:
	@echo "Deploying Pulumi infrastructure..."
	@KUBECONFIG=${KUBE_CONFIG_FILE} PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		pulumi down --yes --skip-preview --refresh --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || \
		KUBECONFIG=${KUBE_CONFIG_FILE} PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} PULUMI_K8S_DELETE_UNREACHABLE=true \
			pulumi down --yes --skip-preview --refresh --stack ${PULUMI_STACK_IDENTIFIER} \
			| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@echo "Deployment complete."

login: pulumi-login
up: pulumi-login pulumi-up wait-all-pods
down: pulumi-login pulumi-down

# ----------------------------------------------------------------------------------------------
# --- Control Flow ---
# ----------------------------------------------------------------------------------------------

# --- Wait for All Pods Ready ---
wait-all-pods:
	@echo "Waiting for all pods in the cluster to be ready..."
	@bash -c 'until [ "$$(kubectl get pods --all-namespaces --no-headers | grep -v "Running\|Completed\|Succeeded" | wc -l)" -eq 0 ]; do echo "Waiting for pods to be ready..."; sleep 5; done'
	@kubectl get pods --all-namespaces --show-labels --kubeconfig ${KUBE_CONFIG_FILE}
	@echo "All pods in the cluster are ready."

# ----------------------------------------------------------------------------------------------
# --- Talos Kubernetes Cluster ---
# ----------------------------------------------------------------------------------------------

# --- Talos Configuration ---
talos-gen-config:
	@echo "Generating Talos Config..."
	@mkdir -p ${HOME}/.kube .kube .pulumi .talos
	@touch ${HOME}/.kube/config ${KUBE_CONFIG_FILE} ${TALOS_CONFIG_FILE}
	@chmod 600 ${HOME}/.kube/config ${KUBE_CONFIG_FILE} ${TALOS_CONFIG_FILE}
	@talosctl gen config kargo https://10.5.0.2:6443 \
		--config-patch @.talos/patch/machine.yaml --output .talos/manifest --force
	@echo "Talos Config generated."
#	@talosctl validate --mode container \
#		--config .talos/manifest/controlplane.yaml
#	@talosctl validate --mode container \
#		--config .talos/manifest/worker.yaml

# --- Talos Cluster ---
talos-cluster: detect-arch talos-gen-config
	@echo "Creating Talos Kubernetes Cluster..."
	@talosctl cluster create \
		--arch=$$(make detect-arch | grep -E "arm64|amd64") \
		--provisioner docker \
		--name talos-kargo-docker \
		--context talos-kargo-docker \
		--controlplanes 1 --memory 2048 \
		--workers 1 --memory-workers 2048 \
		--user-disk "/var/mnt/hostpath-provisioner:4" \
		--init-node-as-endpoint
	@pulumi config set --path kubernetes.distribution talos || true
	@pulumi config set --path kubernetes.context admin@talos-kargo-docker || true
	@pulumi config set --path cilium.enabled false || true
	@pulumi config set --path multus.enabled false || true
	@pulumi config set --path kubernetes.kubeconfig $$(pwd)/.kube/config || true
	@echo "Talos Cluster provisioning..."

# --- Wait for Talos Cluster Ready ---
talos-ready:
	@echo "Waiting for Talos Cluster to be ready..."
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-scheduler --namespace=kube-system --timeout=180s; do echo "Waiting for kube-scheduler to be ready..."; sleep 5; done' || true
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-controller-manager --namespace=kube-system --timeout=180s; do echo "Waiting for kube-controller-manager to be ready..."; sleep 5; done' || true
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-apiserver --namespace=kube-system --timeout=180s; do echo "Waiting for kube-apiserver to be ready..."; sleep 5; done' || true
	@echo "Talos Cluster is ready."

# --- Talos ---
talos: clean-all talos-cluster talos-ready wait-all-pods
	@echo "Talos Cluster ready."

# ----------------------------------------------------------------------------------------------
# --- Maintenance ---
# ----------------------------------------------------------------------------------------------

# --- Cleanup ---
clean: login down
	@echo "Cleaning up resources..."
	@sudo talosctl cluster destroy \
		|| echo "Talos cluster not found."
	@docker rm --force talos-kargo-docker-controlplane-1 talos-kargo-docker-worker-1 \
		|| echo "Talos containers not found."
	@pulumi cancel --yes --stack ${PULUMI_STACK_IDENTIFIER} 2>/dev/null || true
	@pulumi down --yes --skip-preview --refresh --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@rm -rf .talos/manifest/*
	@rm -rf .kube/config
	@echo "Cleanup complete."

clean-all: clean
	@echo "Performing extended cleanup..."
	@echo "Extended cleanup complete."

# --- GitHub Actions Testing ---
act:
	@echo "Testing GitHub Workflows locally..."
	@direnv allow
	@act --container-options "--privileged" --rm \
		--var GITHUB_TOKEN=${GITHUB_TOKEN} \
		--var PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g'
	@echo "GitHub Workflow Test Complete."

# --- Maintain Devcontainer ---
konductor:
	@git submodule update --init .github/konductor
	@git submodule update --remote --merge .github/konductor
	@rsync -av .github/konductor/.devcontainer/* .devcontainer
	@docker pull ghcr.io/containercraft/konductor:latest
	@echo "Devcontainer updated."

test-talos: talos pulumi-up
	@echo "Talos test complete."

# --- Stop Codespaces ---
stop: clean
	@echo "Stopping Codespaces..."
	@gh codespace --codespace ${CODESPACE_NAME} stop
	@echo "Codespaces stopped."

# --- Stop Codespaces ---
force-terminating-ns:
	@kubectl proxy & \
	PROXY_PID=$$! ;\
	sleep 2 ;\
	kubectl get namespaces --field-selector=status.phase=Terminating -o json | jq -r '.items[].metadata.name' | while read NAMESPACE ; do \
		echo "Clearing finalizers for namespace $$NAMESPACE" ;\
		kubectl get namespace $$NAMESPACE -o json | jq '.spec = {"finalizers":[]}' > temp-$$NAMESPACE.json ;\
		curl -k -H "Content-Type: application/json" -X PUT --data-binary @temp-$$NAMESPACE.json 127.0.0.1:8001/api/v1/namespaces/$$NAMESPACE/finalize ;\
		rm -f temp-$$NAMESPACE.json ;\
	done ;\
	kill $$PROXY_PID
