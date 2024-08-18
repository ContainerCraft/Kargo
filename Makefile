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
KUBE_CONFIG_FILE := $$(pwd)/.kube/config
TALOS_CONFIG_FILE := $$(pwd)/.talos/config
PULUMI_HOME := $$(pwd)/.pulumi

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
	@echo "  act              - Test GitHub Actions locally."
	@echo "  stop             - Stop Github Codespaces."

# --- GitHub Actions Testing ---
act:
	@echo "Testing GitHub Workflows locally..."
	@direnv allow
	@act --container-options "--privileged" --rm \
		--var GITHUB_TOKEN=${GITHUB_TOKEN} \
		--var PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN} \
		| sed 's/${ESCAPED_PAT}/***PULUMI_ACCESS_TOKEN***/g'
	@echo "GitHub Workflow Test Complete."

# --- Stop Codespaces ---
stop: clean
	@echo "Stopping Codespaces..."
	@gh codespace --codespace ${CODESPACE_NAME} stop
	@echo "Codespaces stopped."
