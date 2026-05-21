#!/usr/bin/env bash
# Creates a local Kubernetes cluster using kind (Kubernetes IN Docker).
#
# What this script does:
# 1. Checks if a cluster named "crypto-mvp" already exists
# 2. If not, creates one using our port-mapping config
# 3. Sets KUBECONFIG so kubectl talks to this cluster
#
# Usage: bash deployments/dev/kind/create_cluster.sh

set -euo pipefail

CLUSTER_NAME="crypto-mvp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KIND_CONFIG="$SCRIPT_DIR/kind-with-portmapping.yaml"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

# Check if cluster already exists
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "✅ Cluster '$CLUSTER_NAME' already exists."
else
    echo "🚀 Creating kind cluster '$CLUSTER_NAME'..."
    kind create cluster \
        --name "$CLUSTER_NAME" \
        --config "$KIND_CONFIG" \
        --kubeconfig "$KUBECONFIG"
    echo "✅ Cluster '$CLUSTER_NAME' created successfully."
fi

echo ""
echo "📋 Cluster info:"
kubectl cluster-info --context "kind-${CLUSTER_NAME}"
echo ""
echo "📋 Nodes:"
kubectl get nodes
