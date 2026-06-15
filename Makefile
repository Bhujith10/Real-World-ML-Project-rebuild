# Makefile — convenience aliases for common development tasks.
#
# Usage: make <target>
# Example: make build-trades, make deploy-trades, make lint

.PHONY: help lint format test build-trades build-candles deploy-trades deploy-candles cluster kafka kafka-ui risingwave risingwave-views all-infra

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Code Quality ---

lint: ## Run ruff linter on all code
	uv run ruff check .

format: ## Format all code with ruff
	uv run ruff format .

fix: ## Auto-fix lint issues
	uv run ruff check --fix .

# --- Testing ---

test: ## Run all tests
	uv run pytest

# --- Docker ---

build-trades: ## Build trades Docker image and load into kind
	bash scripts/build-and-push-image.sh trades

build-candles: ## Build candles Docker image and load into kind
	bash scripts/build-and-push-image.sh candles


# --- Deployment ---

deploy-trades: ## Deploy trades service to kind cluster
	bash scripts/deploy.sh trades

deploy-candles: ## Deploy candles service to kind cluster
	bash scripts/deploy.sh candles


# --- Infrastructure ---

cluster: ## Create the kind cluster
	bash deployments/dev/kind/create_cluster.sh

kafka: ## Deploy Kafka to the cluster
	bash deployments/dev/kafka/install_kafka.sh

kafka-ui: ## Deploy Kafka UI to the cluster
	bash deployments/dev/kafka/install_kafka_ui.sh

risingwave: ## Deploy RisingWave to the cluster
	bash deployments/dev/risingwave/install.sh

risingwave-views: ## Apply materialized views to RisingWave
	bash deployments/dev/risingwave/apply_views.sh

all-infra: cluster kafka kafka-ui risingwave ## Create cluster + deploy all infrastructure

# --- Pre-commit ---

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	uv run pre-commit run --all-files
