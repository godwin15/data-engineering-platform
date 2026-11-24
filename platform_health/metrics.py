import os
from datetime import datetime, timezone

import clickhouse_connect

from platform_health.yaml_parser import validate_table


class MetricsCollector:

    def __init__(self):
        self.client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            username=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        )

    def collect(self, tables):
        metadata = self.client.query("""
            SELECT
                database,
                name,
                engine,
                total_rows,
                total_bytes
            FROM system.tables
            WHERE database = 'wealth_management'
        """).result_rows

        inventory = {
            f"{database}.{name}": {
                "engine": engine,
                "rows": rows,
                "storage_bytes": size,
            }
            for database, name, engine, rows, size in metadata
        }

        results = []

        for table in sorted(tables):
            validate_table(table)

            metric = {
                "table": table,
                "exists": table in inventory,
                "rows": None,
                "storage_bytes": None,
                "latest_processing_date": None,
                "latest_ingestion": None,
                "freshness_hours": None,
                "errors": [],
            }

            if table not in inventory:
                metric["errors"].append("Table does not exist")
                results.append(metric)
                continue

            metric.update(inventory[table])

            database, name = table.split(".")

            try:
                columns = {
                    row[0] for row in self.client.query(
                        """
                        SELECT name
                        FROM system.columns
                        WHERE database = {db:String}
                          AND table = {tbl:String}
                        """,
                        parameters={
                            "db": database,
                            "tbl": name,
                        },
                    ).result_rows
                }

                expressions = ["count()"]
                fields = ["rows"]

                if "processing_date" in columns:
                    expressions.append(
                        "maxOrNull(toString(processing_date))"
                    )
                    fields.append("latest_processing_date")

                if "ingested_at" in columns:
                    expressions.append(
                        "maxOrNull(toUnixTimestamp(ingested_at))"
                    )
                    fields.append("ingestion_epoch")

                query = (
                    f"SELECT {', '.join(expressions)} "
                    f"FROM {table}"
                )

                values = self.client.query(query).result_rows[0]
                observed = dict(zip(fields, values))

                epoch = observed.pop("ingestion_epoch", None)

                metric.update(observed)

                if epoch is not None:
                    timestamp = datetime.fromtimestamp(
                        epoch, tz=timezone.utc
                    )

                    metric["latest_ingestion"] = timestamp.isoformat()

                    age = (
                        datetime.now(timezone.utc) - timestamp
                    ).total_seconds() / 3600

                    metric["freshness_hours"] = round(age, 2)

            except Exception as exc:
                metric["errors"].append(str(exc))

            results.append(metric)

        return results

    def close(self):
        self.client.close()
