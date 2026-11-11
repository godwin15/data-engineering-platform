import argparse
import os
import sys
from datetime import datetime, timezone

import clickhouse_connect


def parse_datetime(value):
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dag-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--finished-at", required=True)
    parser.add_argument("--error-message", default="")
    args = parser.parse_args()

    started = parse_datetime(args.started_at)
    finished = parse_datetime(args.finished_at)
    duration = (finished - started).total_seconds()

    if duration < 0:
        raise ValueError("Finish time cannot precede start time")

    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )

    client.insert(
        "monitoring.pipeline_runs",
        [[
            args.dag_id,
            args.run_id,
            args.status,
            started,
            finished,
            duration,
            args.error_message,
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

    print(
        f"PIPELINE LOGGED: {args.dag_id} | "
        f"{args.status} | {duration:.2f}s"
    )


if __name__ == "__main__":
    main()
