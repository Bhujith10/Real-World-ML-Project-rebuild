#!/usr/bin/env bash
# Spin up the entire crypto MVP system from scratch.
# Usage: bash scripts/spin-up.sh
#
# This creates a kind cluster, deploys all infrastructure (Kafka, RisingWave,
# MLflow, Grafana), builds service images, and deploys them.
# After running this, the full pipeline is live.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "============================================================"
echo "  Crypto MVP — Full System Spin-Up"
echo "============================================================"
echo ""

# --- Step 1: Create kind cluster ---
echo "==> Step 1: Creating kind cluster..."
bash deployments/dev/kind/create_cluster.sh
echo ""

# --- Step 2: Deploy Kafka ---
echo "==> Step 2: Deploying Kafka..."
bash deployments/dev/kafka/install_kafka.sh
echo ""

# --- Step 3: Deploy Kafka UI ---
echo "==> Step 3: Deploying Kafka UI..."
bash deployments/dev/kafka/install_kafka_ui.sh
echo ""

# --- Step 4: Deploy RisingWave ---
echo "==> Step 4: Deploying RisingWave..."
bash deployments/dev/risingwave/install.sh
echo ""

# --- Step 5: Apply RisingWave materialized views ---
echo "==> Step 5: Applying materialized views..."
echo "    Waiting 15s for RisingWave to be ready..."
sleep 15
bash deployments/dev/risingwave/apply_views.sh
echo ""

# --- Step 6: Deploy MLflow ---
echo "==> Step 6: Deploying MLflow..."
bash deployments/dev/mlflow/install.sh
echo ""

# --- Step 7: Deploy Grafana ---
echo "==> Step 7: Deploying Grafana..."
bash deployments/dev/grafana/install.sh
echo ""

# --- Step 8: Build service images ---
echo "==> Step 8: Building service images..."
bash scripts/build-and-push-image.sh trades
bash scripts/build-and-push-image.sh candles
bash scripts/build-and-push-image.sh predictor
echo ""

# --- Step 9: Deploy services ---
echo "==> Step 9: Deploying services..."
bash scripts/deploy.sh trades
bash scripts/deploy.sh candles
bash scripts/deploy.sh predictor
echo ""

echo "============================================================"
echo "  All systems go!"
echo "============================================================"
echo ""
echo "  Kafka UI:    http://localhost:8182"
echo "  MLflow UI:   http://localhost:5000"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  RisingWave:  psql -h localhost -p 4566 -d dev -U root"
echo ""
echo "  Data should start flowing within 1-2 minutes."
echo "============================================================"
