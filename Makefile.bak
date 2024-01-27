# --- Global Variables ---
ENV=dev
GITHUB_REPOSITORY_STRING := $(shell echo ${GITHUB_REPOSITORY} | tr '[:upper:]' '[:lower:]')
GITHUB_REPO_NAME := $(shell echo ${GITHUB_REPOSITORY_STRING} | awk -F '/' '{print $$2}')
GITHUB_REPO_ORG := $(shell echo ${GITHUB_REPOSITORY_STRING} | awk -F '/' '{print $$1}')
PULUMI_STACK := ${GITHUB_USER}/${GITHUB_REPO_NAME}/${ENV}
PULUMI_ACCESS_TOKEN := ${PULUMI_ACCESS_TOKEN}

# Escape special characters in PULUMI_ACCESS_TOKEN and GITHUB_TOKEN
ESCAPED_PULUMI_ACCESS_TOKEN := $(shell echo "${PULUMI_ACCESS_TOKEN}" | sed -e 's/[\/&]/\\&/g')
ESCAPED_GITHUB_TOKEN := $(shell echo "${GITHUB_TOKEN}" | sed -e 's/[\/&]/\\&/g')

# Basic environment variables
KUBECONFIG := ${PWD}/.kube/config
TALOSCONFIG := ${PWD}/.talos/config

# Basic sanity check to ensure PULUMI_ACCESS_TOKEN is set
ifeq ($(PULUMI_ACCESS_TOKEN),)
$(error PULUMI_ACCESS_TOKEN is not set)
endif

# --- Help ---
# Provides a detailed help message displaying all available commands
help:
	@echo "Available commands in the Kargo project Makefile:"
	@echo "  help             - Display this help message."
	@echo "  login            - Authenticate with Pulumi cloud services."
	@echo "  esc ENV=foobar   - Run Pulumi ESC environment. Default ENV='kubernetes'."
	@echo "  up               - Deploy Pulumi infrastructure using Pulumi stack."
	@echo "  pulumi-down      - Destroy deployed Pulumi infrastructure."
	@echo "  talos-cluster    - Deploy a Talos Kubernetes cluster in Docker."
	@echo "  talos-config     - Generate and validate Talos configuration with patches."
	@echo "  talos            - Create and configure a Talos Kubernetes cluster."
	@echo "  kind             - Create a local Kubernetes cluster using Kind."
	@echo "  clean            - Clean up Pulumi resources and Kind/Talos clusters."
	@echo "  clean-all        - Perform 'clean' and remove Docker volumes."
	@echo "  act              - Test GitHub Actions locally."
	@echo "  konductor        - Update and sync .github/devcontainer submodule."
	@echo "  test             - Run setup tests (kind, up, clean, clean-all)."

# --- Detect Architecture ---
# Function to detect the system architecture
detect-arch = $(shell uname -m | awk '{ if ($$1 == "x86_64") print "amd64"; else if ($$1 == "aarch64" || $$1 == "arm64") print "arm64"; else print "unknown" }')

# --- Pulumi Login Command ---
pulumi-login:
	@echo "Logging in to Pulumi..."
	direnv allow
	@PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} pulumi login 2>&1 | sed 's/$(ESCAPED_PULUMI_ACCESS_TOKEN)/***PULUMI_ACCESS_TOKEN***/g' | sed 's/$(ESCAPED_GITHUB_TOKEN)/***GITHUB_TOKEN***/g'
	@pulumi install
	@echo

# --- Pulumi Login ---
# Login to Pulumi cloud services
login: pulumi-login
	@echo "Login successful."
	@echo

# --- Pulumi ESC ---
# Accepts one argument for Pulumi ESC environment; default is 'kubernetes'
# Usage:
#  - make esc ENV=dev
#  - make esc ENV=test
#  - make esc ENV=prod
esc: login
	$(eval ENV := $(or $(ENV),kubernetes))
	@echo "Running Pulumi ESC environment with argument ${ENV}..."
	@env esc open --format shell ${ENV}
	@echo "Pulumi ESC environment running."
	@echo

# --- Pulumi Up ---
# Deploy Pulumi infrastructure
pulumi-up:
	@echo "Deploying Pulumi infrastructure..."
	@pulumi stack select --create ${PULUMI_STACK}
	@KUBECONFIG=.kube/config PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} pulumi up --yes --skip-preview --refresh --stack ${PULUMI_STACK} 2>&1 | sed 's/$(ESCAPED_PULUMI_ACCESS_TOKEN)/***PULUMI_ACCESS_TOKEN***/g' | sed 's/$(ESCAPED_GITHUB_TOKEN)/***GITHUB_TOKEN***/g' || true
	@sleep 15
	@kubectl get po -A
	@echo "Deployment complete."
	@echo

up: login pulumi-up all-pods-ready

# --- Pulumi Down ---
# Destroy Pulumi infrastructure
pulumi-down: pulumi-login
	@echo "Destroying Pulumi infrastructure..."
	@PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} pulumi down --yes --skip-preview --refresh --stack ${PULUMI_STACK} 2>&1 | sed 's/$(ESCAPED_PULUMI_ACCESS_TOKEN)/***PULUMI_ACCESS_TOKEN***/g' | sed 's/$(ESCAPED_GITHUB_TOKEN)/***GITHUB_TOKEN***/g' || true
	@echo "Infrastructure teardown complete."
	@echo

down: pulumi-down
	@echo "Pulumi infrastructure destroyed."
	@echo

# --- Wait for All Pods Ready ---
# Waits for all pods in the cluster to be ready
all-pods-ready:
	@echo "Waiting for all pods in the cluster to be ready..."
	# Wait for all pods in all namespaces to be ready
	bash -c 'until [ "$$(kubectl get pods --all-namespaces --no-headers | grep -v "Running\|Completed\|Succeeded" | wc -l)" -eq 0 ]; do echo "Waiting for pods to be ready..."; sleep 5; done'
	kubectl get pods --all-namespaces --show-labels --kubeconfig .kube/config
	@echo "All pods in the cluster are ready."
	@echo

# --- Generate Talos Config with Patches ---
# Generates and validates Talos configuration with patches from the .talos/patch directory
talos-gen-config:
	@echo "Generating Talos Config with Patches from .talos/patch directory..."
	@mkdir -p .kube .pulumi .talos
	@touch ${KUBECONFIG} ${TALOSCONFIG}
	@sudo --preserve-env talosctl gen secrets --force --output-file .talos/secrets/secrets.yaml
	@sudo --preserve-env talosctl gen config kargo https://10.5.0.2:6443 --force --with-secrets .talos/secrets/secrets.yaml --config-patch @.talos/patch/machine.yaml --kubernetes-version "1.29.0" --output .talos/manifest --with-examples=false --with-docs=false
	@sudo --preserve-env talosctl validate --mode container --config .talos/manifest/controlplane.yaml
	@sudo --preserve-env talosctl validate --mode container --config .talos/manifest/worker.yaml
	@cat .talos/manifest/talosconfig | tee .talos/config
	@echo "Talos Config Generated in .talos/manifest directory."
	@echo

# --- Create Talos Kubernetes Cluster ---
# Creates a Talos Kubernetes cluster in Docker with architecture detection and configuration patches
#@set -ex; sudo --preserve-env talosctl cluster create --arch=$(ARCH) --provisioner docker --with-debug
# --exposed-ports="80:8080/tcp,443:8443/tcp,2232:2232/tcp,7445:7445/tcp"
talos-cluster:
	@echo "Creating Talos Kubernetes Cluster..."
	@$(eval ARCH := $(detect-arch))
	@echo "Detected Architecture: $(ARCH)"
	@sudo --preserve-env talosctl cluster create --with-debug --wait=false --arch=$(ARCH) --workers 1 --controlplanes 1 --provisioner docker --state=".talos/state" --config-patch '[{"op": "add", "path": "/cluster/proxy", "value": {"disabled": true}}, {"op":"add", "path": "/cluster/network/cni", "value": {"name": "none"}}]'
	@sleep 10
	@echo "Talos Cluster is provisioning..."

talos-load-config:
	@KUBECONFIG=${PWD}.kube/config TALOSCONFIG=${PWD}/.talos/config talosctl config node 10.5.0.2
	@direnv allow; KUBECONFIG=${PWD}.kube/config TALOSCONFIG=${PWD}/.talos/config sudo chown -R $(whoami) .talos .kube .pulumi ${KUBECONFIG} || sudo chown -R runner .talos .kube .pulumi ${KUBECONFIG} ; cat ${KUBECONFIG}
	@direnv allow; KUBECONFIG=${PWD}.kube/config TALOSCONFIG=${PWD}/.talos/config sudo --preserve-env talosctl kubeconfig --force --force-context-name kargo --merge=false ${KUBECONFIG}
	@set -ex; sudo --preserve-env talosctl cluster show
	@echo "Talos Kubernetes Cluster Created."
	@echo

# --- Wait for Talos Ready ---
# Waits for Talos cluster to be ready
# Wait for kube-scheduler to exist and be ready
# Wait for kube-controller-manager to exist and be ready
# Wait for kube-apiserver to exist and be ready
talos-ready:
	@echo "Waiting for Talos Cluster to be ready..."
	@echo
	bash -c 'until kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-scheduler --namespace=kube-system --timeout=180s; do echo "Waiting for kube-scheduler to exist..."; sleep 8; echo; done'
	bash -c 'until kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-controller-manager --namespace=kube-system --timeout=180s; do echo "Waiting for kube-controller-manager to exist..."; sleep 8; echo; done'
	bash -c 'until kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-apiserver --namespace=kube-system --timeout=180s; do echo "Waiting for kube-apiserver to exist..."; sleep 8; echo; done'
	@echo
	kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-scheduler --namespace=kube-system --timeout=180s
	kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-controller-manager --namespace=kube-system --timeout=180s
	kubectl --kubeconfig .kube/config wait --for=condition=Ready pod -l k8s-app=kube-apiserver --namespace=kube-system --timeout=180s
	@echo
	kubectl get pods --kubeconfig .kube/config --namespace kube-system --show-labels
	pulumi config set kubeconfig.context admin@talos-default
	@echo
	@echo "Talos Cluster is ready."
	@echo

# --- Create and Configure Talos Cluster ---
# Wrapper target to generate Talos config and create the cluster
talos: pulumi-login clean clean-all talos-gen-config talos-cluster talos-load-config talos-ready
	@echo "Talos Cluster Created."

# --- Wait for Kind Ready ---
# Waits for Kind cluster to be ready
kind-ready:
	@echo "Waiting for Kind Cluster to be ready..."
	bash -c 'until kubectl -n kube-system get po kube-apiserver-cilium-control-plane &> /dev/null; do echo "Waiting for kube-apiserver-cilium-control-plane to exist..."; sleep 3; done && kubectl wait --for=condition=Ready pod/kube-apiserver-cilium-control-plane --namespace=kube-system --timeout=120s'
	kubectl wait --for=condition=Ready pod -l component=etcd --namespace=kube-system --timeout=180s
	kubectl wait --for=condition=Ready pod -l component=kube-apiserver --namespace=kube-system --timeout=180s
	kubectl wait --for=condition=Ready pod -l component=kube-controller-manager --namespace=kube-system --timeout=180s
	kubectl wait --for=condition=Ready pod -l component=kube-scheduler --namespace=kube-system --timeout=180s
	@echo
	kubectl get pods --all-namespaces --show-labels --kubeconfig .kube/config
	pulumi config set kubeconfig.context kind-cilium
	@echo "Kind Cluster is ready."
	@echo

# --- Create Kind Cluster ---
# Creates a local Kubernetes cluster using Kind
kind-cluster:
	@echo "Creating Kind Cluster..."
	direnv allow
	mkdir -p ${HOME}/.kube .kube || true
	sudo docker volume create cilium-worker-n01
	sudo docker volume create cilium-worker-n02
	sudo docker volume create cilium-control-plane-n01
	sudo kind create cluster --config hack/kind.yaml
	@echo "Waiting for Kind Cluster to be ready..."
	sleep 10
	sudo kind get kubeconfig --name cilium | tee .kube/config >/dev/null
	sudo kind get kubeconfig --name cilium | tee ${HOME}/.kube/config >/dev/null
	@echo "Kind Cluster Created."
	@echo

kind: login kind-cluster kind-ready

# --- Cleanup ---
clean: pulumi-down
	@echo "Cleaning up..."
	sudo --preserve-env kind delete cluster --name cilium || true
	sudo --preserve-env talosctl cluster destroy || true
	sudo --preserve-env talosctl config remove kargo --noconfirm || true
	sudo --preserve-env talosctl config remove kargo-1 --noconfirm || true
	@echo "Cleanup complete."
	@echo

clean-all:
	sudo docker volume rm cilium-worker-n01 || true
	sudo docker volume rm cilium-worker-n02 || true
	sudo docker volume rm cilium-control-plane-n01 || true
	@echo "Extended cleanup complete."
	@echo

## --- GitHub Actions ---
#act: clean-all
#	@echo "Testing GitHub Workflows locally."
#	rm .env
#	echo "GITHUB_TOKEN=${GITHUB_TOKEN}" >> .env
#	echo "PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN}" >> .env
#	PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} sudo --preserve-env act 2>&1 | sed "s/${PULUMI_ACCESS_TOKEN}/***/g"
#	@echo "GitHub Workflow Test Complete."

# --- GitHub Actions ---
act: clean clean-all
	@echo "Testing GitHub Workflows locally."
	@PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} sudo --preserve-env act 2>&1 | sed 's/$(ESCAPED_PULUMI_ACCESS_TOKEN)/***PULUMI_ACCESS_TOKEN***/g' | sed 's/$(ESCAPED_GITHUB_TOKEN)/***GITHUB_TOKEN***/g'
	@echo "GitHub Workflow Test Complete."

# --- Maintain Devcontainer ---
konductor:
	git submodule update --init .github/konductor
	git submodule update --remote --merge .github/konductor
	rsync -av .github/konductor/.devcontainer/* .devcontainer
	docker pull ghcr.io/containercraft/konductor:latest
	@echo

stop:
	@echo "Stopping Github Codespace"
	gh codespace stop --codespace ${CODESPACE_NAME}
	@echo

# --- Testing ---
test-kind: login clean-all kind pulumi-up all-pods-ready clean-all
test-talos: login clean-all talos pulumi-up all-pods-ready clean-all

# --- Default Command ---
all: help
