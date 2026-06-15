#!/usr/bin/env bash
# Applies the materialized views SQL to RisingWave via port-forwarded psql.
#
# Prerequisites:
# - RisingWave must be running in the cluster
# - psql must be installed locally
# - The kind cluster must be running with port mapping on 30456 → 4566
#
# Usage: bash deployments/dev/risingwave/apply_views.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📝 Applying materialized views to RisingWave..."
echo "   Connecting to localhost:4566 (via kind NodePort 30456)..."
echo ""

psql -h localhost -p 4566 -d dev -U root -f "$SCRIPT_DIR/materialized_views.sql"

echo ""
echo "✅ Materialized views applied successfully!"
echo ""
echo "💡 Test with:"
echo "   psql -h localhost -p 4566 -d dev -U root -c 'SELECT * FROM mv_features LIMIT 5;'"
