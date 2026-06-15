#!/usr/bin/env bash
# Deploys RisingWave to the kind cluster as a single-node standalone instance.
#
# What this script does:
# 1. Ensures the risingwavelabs/risingwave image is loaded into the kind cluster
# 2. Applies the risingwave.yaml manifest (Namespace, Deployment, Services)
# 3. Waits for the RisingWave pod to become ready
# 4. Applies the materialized views SQL via psql
#
# RisingWave runs in standalone/single_node mode — suitable for dev.
# It exposes port 4566 (Postgres wire protocol) for SQL queries.
#
# Usage: bash deployments/dev/risingwave/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

RISINGWAVE_IMAGE="risingwavelabs/risingwave:v2.3.0"
CLUSTER_NAME="crypto-mvp"

# Step 1: Ensure image is available in the kind cluster
echo "🔍 Ensuring RisingWave image is loaded into kind cluster..."
if docker exec "$CLUSTER_NAME-control-plane" crictl images 2>/dev/null | grep -q "risingwavelabs/risingwave"; then
    echo "   Image already present in cluster."
else
    echo "   Pulling image and loading into kind..."
    docker pull --platform linux/amd64 "$RISINGWAVE_IMAGE"
    docker save "$RISINGWAVE_IMAGE" | docker exec -i "$CLUSTER_NAME-control-plane" \
        ctr --namespace=k8s.io images import -
    echo "   Image loaded."
fi

# Step 2: Apply Kubernetes manifests
echo ""
echo "📦 Applying RisingWave manifests..."
kubectl apply -f "$SCRIPT_DIR/risingwave.yaml"

# Step 3: Wait for pod to be ready
echo ""
echo "⏳ Waiting for RisingWave pod to become ready (up to 3 minutes)..."
kubectl wait --for=condition=Ready pod -l app=risingwave \
    -n risingwave \
    --timeout=180s

echo ""
echo "✅ RisingWave installed successfully!"
echo ""
echo "📋 RisingWave pods:"
kubectl get pods -n risingwave
echo ""
echo "📋 RisingWave services:"
kubectl get svc -n risingwave
echo ""
echo "💡 Connect with: psql -h localhost -p 4566 -d dev -U root"
