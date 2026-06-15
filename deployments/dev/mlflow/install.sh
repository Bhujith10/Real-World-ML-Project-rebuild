#!/usr/bin/env bash
# Deploys MLflow tracking server to the kind cluster.
#
# What this script does:
# 1. Ensures the MLflow Docker image is loaded into the kind cluster
# 2. Applies the mlflow.yaml manifest (Namespace, PVC, Deployment, Service)
# 3. Waits for the MLflow pod to become ready
#
# MLflow UI accessible at http://localhost:5000 (via NodePort 30500)
#
# Usage: bash deployments/dev/mlflow/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

MLFLOW_IMAGE="ghcr.io/mlflow/mlflow:v2.21.3"
CLUSTER_NAME="crypto-mvp"

# Step 1: Ensure image is available in the kind cluster
echo "🔍 Ensuring MLflow image is loaded into kind cluster..."
if docker exec "$CLUSTER_NAME-control-plane" crictl images 2>/dev/null | grep -q "ghcr.io/mlflow/mlflow"; then
    echo "   Image already present in cluster."
else
    echo "   Pulling image and loading into kind..."
    docker pull --platform linux/amd64 "$MLFLOW_IMAGE"
    docker save "$MLFLOW_IMAGE" | docker exec -i "$CLUSTER_NAME-control-plane" \
        ctr --namespace=k8s.io images import -
    echo "   Image loaded."
fi

# Step 2: Apply Kubernetes manifests
echo ""
echo "📦 Applying MLflow manifests..."
kubectl apply -f "$SCRIPT_DIR/mlflow.yaml"

# Step 3: Wait for pod to be ready
echo ""
echo "⏳ Waiting for MLflow pod to become ready (up to 3 minutes)..."
kubectl wait --for=condition=Ready pod -l app=mlflow \
    -n mlflow \
    --timeout=180s

echo ""
echo "✅ MLflow installed successfully!"
echo ""
echo "📋 MLflow pods:"
kubectl get pods -n mlflow
echo ""
echo "📋 MLflow services:"
kubectl get svc -n mlflow
echo ""
echo "💡 MLflow UI: http://localhost:5000"
