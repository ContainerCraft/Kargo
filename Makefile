# --- Global Variables ---
ENV=dev
GITHUB_REPOSITORY_STRING := $(shell echo ${GITHUB_REPOSITORY} | tr '[:upper:]' '[:lower:]')
GITHUB_REPO_NAME := $(shell echo ${GITHUB_REPOSITORY_STRING} | awk -F '/' '{print $$2}')
GITHUB_REPO_ORG := $(shell echo ${GITHUB_REPOSITORY_STRING} | awk -F '/' '{print $$1}')
PULUMI_STACK := ${GITHUB_USER}/${GITHUB_REPO_NAME}/${ENV}

# --- Help ---
# Provides a default help message displaying all available commands
help:
	@echo "Available commands:"
	@echo "  help                 Display this help message."
	@echo "  login                Authenticate with cloud services."
	@echo "  esc                  Run a Pulumi ESC environment with an optional argument. Default is 'kubernetes'."
	@echo "  up                   Deploy Pulumi IaC program using the stack name 'codespace'."
	@echo "  down                 Destroy Pulumi infrastructure."
	@echo "  kind                 Deploy a local Kubernetes cluster using Kind (Kubernetes-in-Docker)."
	@echo "  talos                Deploy a local Kubernetes cluster using Talos in Docker."
	@echo "  clean                Destroy Pulumi resources, tear down the Kind cluster, and clean up configurations."
	@echo "  clean-all            Perform all actions in 'clean', plus remove Docker volumes."
	@echo "  test                 Run a series of commands to test the setup (kind, up, clean, clean-all)."
	@echo "  act                  Test GitHub Actions locally with the 'gh-act' extension."
	@echo "  devcontainer         Update the .github/devcontainer submodule and sync files."
# --- Help ---
# Provides a detailed help message displaying all available commands
help:
	@echo "Available commands in the Kargo project Makefile:"
	@echo "  help             - Display this help message."
	@echo "  login            - Authenticate with Pulumi cloud services."
	@echo "  esc ENV=foobar   - Run Pulumi ESC environment. Default ENV='kubernetes'."
	@echo "  up               - Deploy Pulumi infrastructure using Pulumi stack."
	@echo "  down             - Destroy deployed Pulumi infrastructure."
	@echo "  talos-cluster    - Deploy a Talos Kubernetes cluster in Docker."
	@echo "  talos-config     - Generate and validate Talos configuration with patches."
	@echo "  talos            - Create and configure a Talos Kubernetes cluster."
	@echo "  kind             - Create a local Kubernetes cluster using Kind."
	@echo "  clean            - Clean up Pulumi resources and Kind/Talos clusters."
	@echo "  clean-all        - Perform 'clean' and remove Docker volumes."
	@echo "  act              - Test GitHub Actions locally."
	@echo "  konductor        - Update and sync .github/devcontainer submodule."
	@echo "  test             - Run setup tests (kind, up, clean, clean-all)."

# --- Pulumi Login Command ---
login:
	@echo "Logging in to Pulumi..."
	direnv allow
	pulumi login
	pulumi install
	@echo "Login successful."

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

# Deploy Pulumi infrastructure
up: login
	@echo "Deploying Pulumi infrastructure..."
	pulumi stack select --create ${PULUMI_STACK}
	pulumi up --yes --skip-preview --stack ${PULUMI_STACK}
	sleep 15
	kubectl get po -A
	@echo "Deployment complete."

# Destroy Pulumi infrastructure
down:
	@echo "Destroying Pulumi infrastructure..."
	pulumi down --yes --skip-preview --stack ${PULUMI_STACK} || true
	@echo "Infrastructure teardown complete."

# --- Detect Architecture ---
# Function to detect the system architecture
detect-arch = $(shell uname -m | awk '{ if ($$1 == "x86_64") print "amd64"; else if ($$1 == "aarch64" || $$1 == "arm64") print "arm64"; else print "unknown" }')

# --- Create Talos Kubernetes Cluster ---
# Creates a Talos Kubernetes cluster in Docker with architecture detection and configuration patches
talos-cluster:
	@echo "Creating Talos Kubernetes Cluster..."
	@$(eval ARCH := $(detect-arch))
	@echo "Detected Architecture: $(ARCH)"
	@talosctl cluster create --wait=false --arch=$(ARCH) --workers 1 --controlplanes 1 --provisioner docker --state=".talos/state" --exposed-ports="80:8080/tcp,443:8443/tcp,7445:7445/tcp" --config-patch '[{"op": "add", "path": "/cluster/proxy", "value": {"disabled": true}}, {"op":"add", "path": "/cluster/network/cni", "value": {"name": "none"}}]'
	@talosctl config node 10.5.0.2
	@talosctl kubeconfig --force --force-context-name kargo --merge=false ${KUBECONFIG}
	@talosctl cluster show
	@kubectl config get-contexts
	@kubectl cluster-info

# --- Generate Talos Config with Patches ---
# Generates and validates Talos configuration with patches from the .talos/patch directory
talos-config:
	@echo "Generating Talos Config with Patches from .talos/patch directory..."
	@rm -rf .talos/{manifest,secret}/*
	@talosctl gen secrets --force --output-file .talos/secret/secrets.yaml
	@talosctl gen config kargo https://10.5.0.2:6443 --force --with-secrets .talos/secret/secrets.yaml --config-patch @.talos/patch/machine.yaml --kubernetes-version "1.29.0" --output .talos/manifest --with-examples=false --with-docs=false
	@talosctl validate --mode container --config .talos/manifest/controlplane.yaml
	@talosctl validate --mode container --config .talos/manifest/worker.yaml
	@echo "Talos Config Generated in .talos/manifest directory."

# --- Create and Configure Talos Cluster ---
# Wrapper target to generate Talos config and create the cluster
talos: talos-config talos-cluster
	@echo "Talos Cluster Created."

# --- Kind ---
kind:
	@echo "Creating Kind Cluster..."
	direnv allow
	docker volume create cilium-worker-n01
	docker volume create cilium-worker-n02
	docker volume create cilium-control-plane-n01
	kind create cluster --config hack/kind.yaml
	kind get kubeconfig --name cilium | tee .kube/config >/dev/null
	sleep 5
	kubectl get po -A
	@echo "Kind Cluster Created."

# --- Cleanup ---
clean: down
	@echo "Cleaning up..."
	talosctl cluster destroy || true
	talosctl config remove kargo --noconfirm || true
	talosctl config remove kargo-1 --noconfirm || true
	kind delete cluster --name cilium || true
	rm -rf .kube/config || true
	rm -rf .kube/config || true
	@echo "Cleanup complete."

clean-all: clean
	docker volume rm cilium-worker-n01 || true
	docker volume rm cilium-worker-n02 || true
	docker volume rm cilium-control-plane-n01 || true
	@echo "Extended cleanup complete."

# --- GitHub Actions ---
act:
	@echo "Testing GitHub Workflows locally."
	act -s GITHUB_TOKEN=${GITHUB_TOKEN} -s ACTIONS_RUNTIME_TOKEN=${GITHUB_TOKEN} -s GHA_GITHUB_TOKEN=${GITHUB_TOKEN}
	@echo "GitHub Workflow Test Complete."

# --- Maintain Devcontainer ---
konductor:
	git submodule update --init --recursive .github/konductor
	git submodule update --remote --merge .github/konductor
	rsync -av .github/konductor/.devcontainer/* .devcontainer

# --- Testing ---
test: kind up clean clean-all

# --- Default Command ---
all: help
