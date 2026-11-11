import logging
import os
from datetime import datetime, timezone

import clickhouse_connect

logger = logging.getLogger(__name__)


def record_pipeline_run(context, status):
    dag_run = context["dag_run"]

    started = dag_run.start_date
    finished = dag_run.end_date or datetime.now(timezone.utc)

    if started is None:
        logger.warning("Missing DAG start time; skipping monitoring")
        return

    error_message = ""

    if status == "failed":
        task_instance = context.get("task_instance")
        exception = context.get("exception")

        if task_instance:
            error_message = f"Failed task: {task_instance.task_id}"

        if exception:
            error_message += f" | {exception}"

    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )

    try:
        client.insert(
            "monitoring.pipeline_runs",
            [[
                dag_run.dag_id,
                dag_run.run_id,
                status,
                started,
                finished,
                max(0, (finished - started).total_seconds()),
                error_message,
                datetime.now(timezone.utc),
            ]],
            column_names=[
                "dag_id",
                "run_id",
                "status",
                "started_at",
                "finished_at",
                "duration_seconds",
                "error_message",
                "recorded_at",
            ],
        )
        logger.info(
            "Pipeline monitoring recorded: %s | %s",
            dag_run.dag_id,
            status,
        )
    finally:
        client.close()


def safe_record_pipeline_run(context, status):
    try:
        record_pipeline_run(context, status)
    except Exception:
        logger.exception("Unable to record pipeline monitoring metric")


def on_pipeline_success(context):
    safe_record_pipeline_run(context, "success")


def on_pipeline_failure(context):
    safe_record_pipeline_run(context, "failed")
