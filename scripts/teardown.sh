#!/usr/bin/env bash
# Tear down the entire crypto MVP system.
# Usage: bash scripts/teardown.sh
#
# This deletes the kind cluster and all resources within it.
# Local files (parquet data, code) are NOT affected.

set -euo pipefail

echo "============================================================"
echo "  Crypto MVP - Teardown"
echo "============================================================"
echo ""

CLUSTER_NAME="crypto-mvp"

if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "==> Deleting kind cluster '${CLUSTER_NAME}'..."
    kind delete cluster --name "$CLUSTER_NAME"
    echo "==> Cluster deleted."
else
    echo "==> Cluster '${CLUSTER_NAME}' does not exist. Nothing to do."
fi

echo ""
echo "============================================================"
echo "  Teardown complete."
echo "  Your local data/ and code are untouched."
echo "  Run 'bash scripts/spin-up.sh' to recreate everything."
echo "============================================================"
