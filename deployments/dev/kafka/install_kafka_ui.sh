#!/usr/bin/env bash
# Deploys Kafka UI to the kind cluster.
#
# What this script does:
# 1. Ensures the provectuslabs/kafka-ui image is loaded into the kind cluster
# 2. Applies the kafka-ui.yaml manifest (Deployment + NodePort Service)
# 3. Waits for the Kafka UI pod to become ready
#
# After running this, open http://localhost:8182 in your browser to see Kafka UI.
#
# Usage: bash deployments/dev/kafka/install_kafka_ui.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

KAFKA_UI_IMAGE="provectuslabs/kafka-ui:latest"
CLUSTER_NAME="crypto-mvp"

# Step 1: Ensure image is available in the kind cluster
echo "🐳 Ensuring Kafka UI image is loaded into kind cluster..."
if docker exec "$CLUSTER_NAME-control-plane" crictl images 2>/dev/null | grep -q "kafka-ui"; then
    echo "   Image already present in cluster."
else
    echo "   Pulling image and loading into kind..."
    docker pull "$KAFKA_UI_IMAGE"
    docker save "$KAFKA_UI_IMAGE" | docker exec -i "$CLUSTER_NAME-control-plane" \
        ctr --namespace=k8s.io images import -
    echo "   Image loaded."
fi

# Step 2: Apply Kubernetes manifests
echo ""
echo "📦 Applying Kafka UI manifests..."
kubectl apply -f "$SCRIPT_DIR/kafka-ui.yaml"

# Step 3: Wait for pod to be ready
echo ""
echo "⏳ Waiting for Kafka UI pod to become ready..."
kubectl wait --for=condition=Ready pod \
    -l app=kafka-ui \
    -n kafka \
    --timeout=60s

echo ""
echo "✅ Kafka UI installed successfully!"
echo "🌐 Open http://localhost:8182 in your browser"
