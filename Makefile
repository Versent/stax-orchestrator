SHELL = /bin/bash
SHELLFLAGS = -ex

export APP_NAME			:= stax-orchestrator
export APP_DESCRIPTION	:= 'Stax Workloads Orchestrator - Interact with Stax to deploy workloads into your AWS Account(s).'
export APP_AUTHOR		:= Versent
export APP_VERSION		:= 0.1.0

help: ## Get help about Makefile commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
