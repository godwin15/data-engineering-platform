#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

source .venv/bin/activate

set -a
source .env
set +a

export PYTHONPATH=.

echo "=== CONFIGURATION VALIDATION ==="
python scripts/validate_quality_configs.py

echo "=== OFFLINE UNIT TESTS ==="
python -m unittest discover -s tests/data_quality -v

echo "=== INITIALIZE SYNTHETIC TEST DATA ==="
docker exec -i de_clickhouse clickhouse-client \
    --multiquery < tests/integration/setup_test_data.sql

echo "=== LIVE CORRUPTION TESTS ==="
python tests/integration/test_corruption_scenarios.py

echo "=== PRODUCTION QUALITY CHECKS ==="
CLICKHOUSE_HOST=localhost CLICKHOUSE_PORT=8123 \
    python -m data_quality.runner

echo "=== ALL DATA QUALITY VALIDATIONS PASSED ==="
