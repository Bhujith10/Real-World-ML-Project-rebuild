#!/usr/bin/env bash
# Deploy a service to the kind cluster.
#
# Usage:
#   bash scripts/deploy.sh trades
#   bash scripts/deploy.sh candles
#
# What it does:
# 1. Applies the Kubernetes manifests for the service
# 2. Restarts the deployment to pick up new image changes
# 3. Waits for the pod to become ready
#
# Prerequisites: kind cluster running, image loaded (run build-and-push-image.sh first)

set -euo pipefail

SERVICE_NAME="${1:?Usage: $0 <service-name>}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

DEPLOY_DIR="$PROJECT_ROOT/deployments/dev/$SERVICE_NAME"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ No deployment directory found at $DEPLOY_DIR"
    exit 1
fi

echo "📦 Applying manifests from $DEPLOY_DIR..."
kubectl apply -f "$DEPLOY_DIR/deployment.yaml"

echo ""
echo "🔄 Restarting deployment '$SERVICE_NAME'..."
kubectl rollout restart deployment "$SERVICE_NAME" 2>/dev/null || true

echo ""
echo "⏳ Waiting for pod to become ready..."
kubectl wait --for=condition=Ready pod \
    -l app="$SERVICE_NAME" \
    --timeout=60s

echo ""
echo "✅ Service '$SERVICE_NAME' deployed successfully!"
echo ""
echo "📋 Pods:"
kubectl get pods -l app="$SERVICE_NAME"
