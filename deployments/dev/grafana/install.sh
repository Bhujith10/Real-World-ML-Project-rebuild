#!/usr/bin/env bash
# Deploy Grafana to the kind cluster.
# Usage: bash deployments/dev/grafana/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deploying Grafana..."
kubectl apply -f "$SCRIPT_DIR/grafana.yaml"
kubectl rollout status deployment/grafana -n grafana --timeout=120s
echo "==> Grafana is running at http://localhost:3000 (admin/admin)"
