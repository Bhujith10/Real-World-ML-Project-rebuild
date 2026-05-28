#!/usr/bin/env bash
# Build a Docker image for a service and load it into the kind cluster.
#
# Usage:
#   bash scripts/build-and-push-image.sh trades
#   bash scripts/build-and-push-image.sh candles
#
# What it does:
# 1. Builds the Docker image from the service's Dockerfile
# 2. Loads it into the kind cluster (so Kubernetes can use it)
#
# In production, step 2 would push to a container registry (GHCR) instead.

set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service-name>}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_NAME="crypto-mvp"
IMAGE_TAG="${SERVICE_NAME}:dev"

SERVICE_DIR="$PROJECT_ROOT/services/$SERVICE_NAME"

if [ ! -f "$SERVICE_DIR/Dockerfile" ]; then
    echo "❌ No Dockerfile found at $SERVICE_DIR/Dockerfile"
    exit 1
fi

echo "🔨 Building image '$IMAGE_TAG' from $SERVICE_DIR..."
docker build -t "$IMAGE_TAG" -f "$SERVICE_DIR/Dockerfile" "$SERVICE_DIR"

echo ""
echo "📦 Loading image into kind cluster '$CLUSTER_NAME'..."
docker save "$IMAGE_TAG" | docker exec -i "$CLUSTER_NAME-control-plane" \
    ctr --namespace=k8s.io images import -

echo ""
echo "✅ Image '$IMAGE_TAG' built and loaded into kind cluster."
