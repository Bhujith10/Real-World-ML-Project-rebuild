#!/usr/bin/env bash
# Deploys Apache Kafka to the kind cluster using plain K8s manifests + the official Apache image.
#
# What this script does:
# 1. Ensures the apache/kafka:3.9.0 image is loaded into the kind cluster
# 2. Applies the kafka.yaml manifest (Namespace, ConfigMap, Services, StatefulSet)
# 3. Waits for the Kafka pod to become ready
#
# We use the official Apache Kafka image in KRaft mode (no ZooKeeper needed since Kafka 3.3+).
# Bitnami images were removed from Docker Hub in 2025, so we use the official image directly.
#
# Usage: bash deployments/dev/kafka/install_kafka.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export KUBECONFIG="$PROJECT_ROOT/kubeconfig"

KAFKA_IMAGE="apache/kafka:3.9.0"
CLUSTER_NAME="crypto-mvp"

# Step 1: Ensure image is available in the kind cluster
echo "� Ensuring Kafka image is loaded into kind cluster..."
if docker exec "$CLUSTER_NAME-control-plane" crictl images 2>/dev/null | grep -q "apache/kafka"; then
    echo "   Image already present in cluster."
else
    echo "   Pulling image and loading into kind..."
    docker pull --platform linux/amd64 "$KAFKA_IMAGE"
    docker save "$KAFKA_IMAGE" | docker exec -i "$CLUSTER_NAME-control-plane" \
        ctr --namespace=k8s.io images import -
    echo "   Image loaded."
fi

# Step 2: Apply Kubernetes manifests
echo ""
echo "📦 Applying Kafka manifests..."
kubectl apply -f "$SCRIPT_DIR/kafka.yaml"

# Step 3: Wait for pod to be ready
echo ""
echo "⏳ Waiting for Kafka pod to become ready (up to 2 minutes)..."
kubectl wait --for=condition=Ready pod/kafka-0 \
    -n kafka \
    --timeout=120s

echo ""
echo "✅ Kafka installed successfully!"
echo ""
echo "📋 Kafka pods:"
kubectl get pods -n kafka
echo ""
echo "📋 Kafka services:"
kubectl get svc -n kafka
