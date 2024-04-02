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
TALOS_CONFIG_FILE := ${PWD}/.talos/config
KUBE_CONFIG_FILE := ${PWD}/.kube/config

# Check if PULUMI_ACCESS_TOKEN is set
ifeq ($(ESCAPED_PAT),)
$(warning PULUMI_ACCESS_TOKEN is not set)
endif

# Check if GITHUB_TOKEN is set
ifeq ($(ESCAPED_GITHUB_TOKEN),)
$(warning GITHUB_TOKEN is not set)
endif

# --- Targets ---
.PHONY: help detect-arch pulumi-login pulumi-up up talos-gen-config talos-cluster kind-cluster clean clean-all act konductor test-kind test-talos stop force-terminating-ns

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
		pulumi up --yes --skip-preview --refresh --stack ${PULUMI_STACK_IDENTIFIER} \
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
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-scheduler --namespace=kube-system --timeout=180s; do echo "Waiting for kube-scheduler to be ready..."; sleep 5; done'
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-controller-manager --namespace=kube-system --timeout=180s; do echo "Waiting for kube-controller-manager to be ready..."; sleep 5; done'
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l k8s-app=kube-apiserver --namespace=kube-system --timeout=180s; do echo "Waiting for kube-apiserver to be ready..."; sleep 5; done'
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
	@direnv allow
	@mkdir -p ${HOME}/.kube .kube || true
	@touch ${HOME}/.kube/config .kube/config || true
	@chmod 600 ${HOME}/.kube/config .kube/config || true
	@sudo docker volume create kargo-worker-n01
	@sudo docker volume create kargo-worker-n02
	@sudo docker volume create kargo-control-plane-n01
	@sudo kind create cluster --wait 1m --retain --config=hack/kind.yaml
	@sudo kind get clusters
	@sudo kind get kubeconfig --name kargo | tee ${KUBE_CONFIG_FILE} 1>/dev/null
	@sudo kind get kubeconfig --name kargo | tee ${HOME}/.kube/config 1>/dev/null
	@sudo chown -R $(id -u):$(id -g) ${KUBE_CONFIG_FILE}
	@pulumi config set kubernetes kind || true
	@echo "Created Kind Cluster."

# --- Wait for Kind Cluster Ready ---
kind-ready:
	@echo "Waiting for Kind Kubernetes API to be ready..."
	@kubectl get all --all-namespaces --show-labels --kubeconfig ${KUBE_CONFIG_FILE} || sleep 5
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l component=kube-apiserver --namespace=kube-system --timeout=180s; do echo "Waiting for kube-apiserver to be ready..."; sleep 5; done'
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l component=kube-scheduler --namespace=kube-system --timeout=180s; do echo "Waiting for kube-scheduler to be ready..."; sleep 5; done'
	@bash -c 'until kubectl --kubeconfig ${KUBE_CONFIG_FILE} wait --for=condition=Ready pod -l component=kube-controller-manager --namespace=kube-system --timeout=180s; do echo "Waiting for kube-controller-manager to be ready..."; sleep 5; done'
	@echo "Kind Cluster is ready."

kind: login kind-cluster kind-ready

# ----------------------------------------------------------------------------------------------
# --- Maintenance ---
# ----------------------------------------------------------------------------------------------

# --- Cleanup ---
clean: login down
	@echo "Cleaning up resources..."
	@sudo kind delete cluster --name kargo \
		|| echo "Kind cluster not found."
	@sudo kind delete cluster --name kind \
		|| echo "Kind cluster not found."
	@sudo talosctl cluster destroy \
		|| echo "Talos cluster not found."
	@echo "Cleanup complete."

clean-all: clean
	@echo "Performing extended cleanup..."
	@sudo docker volume rm kargo-worker-n01 kargo-worker-n02 kargo-control-plane-n01 \
		|| echo "Docker volumes not found."
	@rm -rf Pulumi.*.yaml
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
