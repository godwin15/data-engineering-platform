import os
from datetime import datetime, timezone
from uuid import uuid4

import clickhouse_connect


def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )


def log_quality_metric(
    pipeline_name,
    table_name,
    check_name,
    metric_value,
    status,
    expected_value=None,
    details="",
    run_id=None,
):
    run_id = run_id or os.getenv("AIRFLOW_CTX_DAG_RUN_ID") or str(uuid4())

    client = get_client()

    client.insert(
        "monitoring.data_quality_metrics",
        [[
            run_id,
            pipeline_name,
            table_name,
            check_name,
            float(metric_value),
            float(expected_value) if expected_value is not None else None,
            status,
            details,
            datetime.now(timezone.utc),
        ]],
        column_names=[
            "run_id",
            "pipeline_name",
            "table_name",
            "check_name",
            "metric_value",
            "expected_value",
            "status",
            "details",
            "checked_at",
        ],
    )

    print(f"METRIC LOGGED: {pipeline_name} | {check_name} | {status}")
