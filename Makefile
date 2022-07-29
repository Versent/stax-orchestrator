SHELL = /bin/bash
SHELLFLAGS = -ex

APP_NAME			     := stax-orchestrator
APP_DESCRIPTION	         := 'Stax Workloads Orchestrator - Interact with Stax to deploy workloads into your AWS Account(s).'
APP_AUTHOR		         := Versent
APP_VERSION		         := 0.1.0
ARTIFACT_BUCKET_NAME     := $(shell aws ssm get-parameter --name /orchestrator/stax/artifact/bucket/name --query Parameter.Value --output text)
GIT_HASH                  ?= $(shell git rev-parse --short HEAD)
GIT_BRANCH               ?= $(shell git rev-parse --abbrev-ref HEAD)

help: ## Get help about Makefile commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

install-dependencies: ## Install project dependencies using pipenv
	pipenv install --dev
.PHONY: install-dependencies

shell: ## Spawn a shell in the current virtual environment
	pipenv shell
.PHONY: shell

lint: ## Lint python files with black, pylint and check imports with isort
	pipenv run isort --check-only --diff functions src
	pipenv run black --check --diff functions src
	pipenv run pylint --fail-under=10.0 functions src
.PHONY: lint

format: ## Format python files with black and fix imports with isort
	pipenv run isort functions src
	pipenv run black functions src
.PHONY: format

prepare-lambda-layer-dir: clean ## Build lambda layer with shared dependencies
	mkdir -p lambda_layer
	pipenv requirements > requirements.txt
	pip install -r requirements.txt -t lambda_layer
	cp -R src/* lambda_layer
.PHONY: prepare-lambda-layer-dir

build-app: prepare-lambda-layer-dir ## Use docker and sam to build the app locally
	sam build --use-container
.PHONY: build-app

run-create-workload-lambda-locally: ## Invoke CreateWorkloadLambda running in a docker container locally
	sam local invoke CreateWorkloadLambda -e events/create_workload_innovation.json
.PHONY: run-create-workload-lambda-locally

clean: ## Cleanup local artifacts
	rm -rf requirements.txt lambda_layer
.PHONY: clean

deploy-stax-orchestrator: ## Deploy Stax Orchestrator
	$(info [+] Deploying Stax Orchestrator...)
	@sam deploy --no-fail-on-empty-changeset \
		--stack-name orchestrator-stax \
		--capabilities CAPABILITY_NAMED_IAM \
		--tags "orchestrator-stax:branch=$(GIT_BRANCH)" "orchestrator-stax:version=$(GIT_HASH)" \
		--template-file template.yml \
		--s3-bucket $(ARTIFACT_BUCKET_NAME)
	# @make clean
.PHONY: deploy-stax-orchestrator
