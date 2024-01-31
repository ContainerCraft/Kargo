# --- Global Variables ---
KUBEDIR ?= .kube
KUBECONFIG ?= ${KUBEDIR}/config
# Escape special characters in sensitive tokens
ESCAPED_PAT := $(shell echo "${PULUMI_ACCESS_TOKEN}" | sed -e 's/[\/&]/\\&/g')
ESCAPED_GITHUB_TOKEN := $(shell echo "${GITHUB_TOKEN}" | sed -e 's/[\/&]/\\&/g')

# Check if PULUMI_ACCESS_TOKEN is set
ifeq ($(ESCAPED_PAT),)
$(warning PULUMI_ACCESS_TOKEN is not set)
endif

# Check if GITHUB_TOKEN is set
ifeq ($(ESCAPED_GITHUB_TOKEN),)
$(warning GITHUB_TOKEN is not set)
endif

LOWERCASE_GITHUB_REPOSITORY := $(shell echo ${GITHUB_REPOSITORY} | tr '[:upper:]' '[:lower:]')
REPO_NAME := $(shell echo ${LOWERCASE_GITHUB_REPOSITORY} | awk -F '/' '{print $$2}')
REPO_ORG := $(shell echo ${LOWERCASE_GITHUB_REPOSITORY} | awk -F '/' '{print $$1}')
PROJECT ?= $(or $(REPO_NAME),kargo)
STACK ?= $(or $(ENVIRONMENT),dev)

##################################################################################
# If PULUMI_BACKEND_URL starts with 'file://'; then
#	Set ORGANIZATION to `organization` if PULUMI_BACKEND_URL starts with 'file://'
#	Set Pulumi stack identifier to <organization>/<project>/<deployment>
# Else
#	Set ORGANIZATION to GITHUB_USER or fallback to 'organization'
#	Set Pulumi stack identifier to `dev`
ifeq ($(findstring file://,$(PULUMI_BACKEND_URL)),file://)
	ORGANIZATION = "organization"
	PULUMI_STACK_IDENTIFIER := $(or $(ORGANIZATION),organization)/$(or $(PROJECT),kargo)/$(or $(STACK),dev)
$(info ORGANIZATION: set to fallback string: ORGANIZATION=${ORGANIZATION})
$(info PROJECT: set to fallback string: PROJECT=${PROJECT})
$(info STACK: set to fallback string: STACK=${STACK})
else
	ORGANIZATION = $(or $(GITHUB_ORG), $(GITHUB_USER),organization)
	PULUMI_STACK_IDENTIFIER := 'dev'
$(info ORGANIZATION: set to string: ORGANIZATION=${ORGANIZATION})
$(info PROJECT: set to string: PROJECT=${PROJECT})
$(info STACK: set to string: STACK=${STACK})
endif

##################################################################################
# Set Pulumi organization to REPO Org name, GITHUB_USER, or fallback to 'organization'
# ORGANIZATION ?= $(or $(REPO_ORG), $(GITHUB_USER),organization)

# --- Targets ---
.PHONY: help detect-arch pulumi-login pulumi-up up talos-gen-config talos-cluster kind-cluster clean clean-all act konductor test-kind test-talos stop

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
	@echo "  kind             - Create a local Kubernetes cluster using Kind."
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
	@pulumi login | sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' || true
	@pulumi install | grep -v already || true
	@pulumi stack select --create ${PULUMI_STACK_IDENTIFIER} || true
	@echo "Login successful."

# --- Pulumi Deployment ---
pulumi-up:
	@echo "Deploying Pulumi infrastructure..."
	@pulumi up --yes --skip-preview --refresh --stack ${PULUMI_STACK_IDENTIFIER} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g'
	@echo "Deployment complete."

pulumi-down:
	@echo "Deploying Pulumi infrastructure..."
	@pulumi down --yes --skip-preview --refresh \
	| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' \
		|| PULUMI_K8S_DELETE_UNREACHABLE=true \
		pulumi down --yes --skip-preview --refresh \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g' \
			|| true
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
	@bash -c "until [ \"$$(kubectl get pods --all-namespaces --no-headers --kubeconfig $${KUBECONFIG} | grep -vE 'Running|Completed|Succeeded' | wc -l)\" -eq 0 ]; do echo \"Waiting for pods to be ready...\"; sleep 5; done"
	@echo "All pods in the cluster are ready."

# ----------------------------------------------------------------------------------------------
# --- Talos Kubernetes Cluster ---
# ----------------------------------------------------------------------------------------------

# --- Talos Configuration ---
talos-gen-config:
	@echo "Generating Talos Config..."
	@mkdir -p ${HOME}/.kube .kube .pulumi .talos
	@touch ${KUBECONFIG} $${TALOSCONFIG}
	@chmod 600 ${KUBECONFIG} $${TALOSCONFIG}
	@sudo talosctl gen config kargo https://10.5.0.2:6443 \
		--config-patch @.talos/patch/machine.yaml --output .talos/manifest
	@sudo talosctl validate --mode container \
		--config .talos/manifest/controlplane.yaml
	@echo "Talos Config generated."

# --- Talos Cluster ---
talos-cluster: detect-arch talos-gen-config
	@echo "Creating Talos Kubernetes Cluster..."
	@sudo talosctl cluster create \
		--arch=$$(make detect-arch) \
		--workers 1 \
		--controlplanes 1 \
		--provisioner docker
	@pulumi config set kubernetes talos || true
	@echo "Talos Cluster provisioning..."

# --- Wait for Talos Cluster Ready ---
talos-ready:
	@echo "Waiting for Talos Cluster to be ready..."
	@bash -c 'until kubectl wait --for=condition=Ready pod -l k8s-app=kube-scheduler --namespace=kube-system --timeout=180s; do echo "Waiting for kube-scheduler to be ready..."; sleep 5; done'
	@bash -c 'until kubectl wait --for=condition=Ready pod -l k8s-app=kube-controller-manager --namespace=kube-system --timeout=180s; do echo "Waiting for kube-controller-manager to be ready..."; sleep 5; done'
	@bash -c 'until kubectl wait --for=condition=Ready pod -l k8s-app=kube-apiserver --namespace=kube-system --timeout=180s; do echo "Waiting for kube-apiserver to be ready..."; sleep 5; done'
	@echo "Talos Cluster is ready."

# --- Talos ---
talos: clean-all talos-cluster talos-ready wait-all-pods
	@echo "Talos Cluster ready."

# ----------------------------------------------------------------------------------------------
# --- Kind Kubernetes Cluster ---
# ----------------------------------------------------------------------------------------------

# --- Kind Cluster ---
kind-cluster:
	@echo "Creating Kind Cluster..."
	@sudo docker volume create cilium-worker-n01
	@sudo docker volume create cilium-worker-n02
	@sudo docker volume create cilium-control-plane-n01
	@echo \
		&& rm -rf ${KUBECONFIG} \
		&& mkdir -p ${KUBEDIR} \
		&& touch ${KUBECONFIG} \
		&& chmod 600 ${KUBECONFIG} \
		&& sudo chown -R $$(whoami):$$(whoami) ${KUBECONFIG}
	@sudo kind create cluster --retain --config=hack/kind.yaml --kubeconfig ${KUBECONFIG}
	@echo "Kind Kubernetes Clusters: $$(sudo kind get clusters || true)"
	@kubectl get all --all-namespaces --kubeconfig ${KUBECONFIG} || true
	@pulumi config set kubernetes kind || true
	@echo "Created Kind Cluster."

# --- Wait for Kind Cluster Ready ---
kind-ready:
	@echo "Waiting for Kind Kubernetes API to be ready..."
	@printenv
	@echo ${KUBECONFIG}
	@cat ${KUBECONFIG}
	@set -x; bash -c 'COUNT=0; until kubectl wait --for=condition=Ready pod -l component=kube-apiserver --namespace=kube-system --timeout=180s --kubeconfig ${KUBECONFIG}; do echo "Waiting for kube-apiserver to be ready..."; sleep 8; ((COUNT++)); if [[ $$COUNT -ge 10 ]]; then echo "kube-apiserver is not ready after 12 attempts. Exiting with error."; exit 1; fi; done'
	@set -ex; kubectl wait --for=condition=Ready pod -l component=kube-apiserver --namespace=kube-system --timeout=180s --kubeconfig .kube/config
	@set -x; bash -c "until kubectl wait --for=condition=Ready pod -l component=kube-scheduler --namespace=kube-system --timeout=180s --kubeconfig ${KUBECONFIG}; do echo 'Waiting for kube-scheduler to be ready...'; sleep 5; done"
	@set -x; bash -c "until kubectl wait --for=condition=Ready pod -l component=kube-controller-manager --namespace=kube-system --timeout=180s --kubeconfig ${KUBECONFIG}; do echo 'Waiting for kube-controller-manager to be ready...'; sleep 5; done"
	@echo "Kind Cluster is ready."

kind: login kind-cluster kind-ready

# ----------------------------------------------------------------------------------------------
# --- Maintenance ---
# ----------------------------------------------------------------------------------------------

# --- Cleanup ---
clean: login down
	@echo "Cleaning up resources..."
	@sudo kind delete cluster --name cilium \
		|| echo "Kind cluster not found."
	@sudo kind delete cluster --name kind \
		|| echo "Kind cluster not found."
	@sudo talosctl cluster destroy \
		|| echo "Talos cluster not found."
	@echo "Cleanup complete."

clean-all: clean
	@echo "Performing extended cleanup..."
	@sudo docker volume rm cilium-worker-n01 cilium-worker-n02 cilium-control-plane-n01 \
		|| echo "Docker volumes not found."
	@rm -rf Pulumi.*.yaml
	@echo "Extended cleanup complete."

# --- GitHub Actions Testing ---
act: clean
	@echo "Testing GitHub Workflows locally..."
	@export GITHUB_TOKEN=${GITHUB_TOKEN}; export PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN}; \
		act --container-options "--privileged" --rm \
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

# --- Testing ---
test-kind: kind pulumi-up
	@echo "Kind test complete."

test-talos: talos pulumi-up
	@echo "Talos test complete."

# --- Stop Codespaces ---
stop: clean
	@echo "Stopping Codespaces..."
	@gh codespace --codespace ${CODESPACE_NAME} stop
	@echo "Codespaces stopped."
