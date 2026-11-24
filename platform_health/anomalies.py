from pathlib import Path

import yaml


def load_thresholds(path="configs/health/thresholds.yaml"):
    return yaml.safe_load(Path(path).read_text())


def make_alert(table, rule, severity, message):
    return {
        "table": table,
        "rule": rule,
        "severity": severity,
        "message": message,
    }


def detect_anomalies(metrics, graph, previous, config, parser_errors=None):
    alerts = []

    for metric in metrics:
        table = metric["table"]

        def alert(rule, severity, message):
            alerts.append(
                make_alert(table, rule, severity, message)
            )

        if not metric["exists"]:
            alert("missing_table", "CRITICAL", "Table does not exist")
            continue

        if metric["errors"]:
            alert(
                "collection_error",
                "CRITICAL",
                "; ".join(metric["errors"]),
            )
            continue

        rows = metric["rows"]
        age = metric["freshness_hours"]
        size = metric["storage_bytes"]

        freshness = config["freshness"]
        volume = config["volume"]
        storage = config["storage"]

        if age is None:
            if config["monitoring"]["alert_on_unknown_freshness"]:
                alert(
                    "unknown_freshness",
                    "WARNING",
                    "Ingestion timestamp unavailable",
                )
        elif age < 0:
            alert(
                "clock_skew",
                "WARNING",
                "Ingestion timestamp is in the future",
            )
        elif age > freshness["critical_hours"]:
            alert(
                "stale_data",
                "CRITICAL",
                f"Last ingestion was {age:.2f} hours ago",
            )
        elif age > freshness["warning_hours"]:
            alert(
                "stale_data",
                "WARNING",
                f"Last ingestion was {age:.2f} hours ago",
            )

        if rows is None:
            alert("unknown_volume", "WARNING", "Row count unavailable")
        elif rows < volume["minimum_rows"]:
            alert("empty_table", "CRITICAL", f"Only {rows} rows")

        if size is None:
            if config["monitoring"]["alert_on_unknown_storage"]:
                alert(
                    "unknown_storage",
                    "WARNING",
                    "Storage size unavailable from ClickHouse",
                )

        baseline = previous.get(table, {})

        old_rows = baseline.get("rows")

        if rows is not None and old_rows is not None:
            if old_rows > 0:
                change = (rows - old_rows) / old_rows * 100

                if abs(change) >= volume["critical_change_pct"]:
                    severity = "CRITICAL"
                elif abs(change) >= volume["warning_change_pct"]:
                    severity = "WARNING"
                else:
                    severity = None

                if severity:
                    alert(
                        "volume_change",
                        severity,
                        f"Rows changed {change:+.2f}% "
                        f"({old_rows} -> {rows})",
                    )

        old_size = baseline.get("storage_bytes")

        if size is not None and old_size is not None:
            if old_size > 0:
                growth = (size - old_size) / old_size * 100

                if growth >= storage["critical_growth_pct"]:
                    severity = "CRITICAL"
                elif growth >= storage["warning_growth_pct"]:
                    severity = "WARNING"
                else:
                    severity = None

                if severity:
                    alert(
                        "storage_growth",
                        severity,
                        f"Storage grew {growth:.2f}%",
                    )

    for table in graph.orphan_tables():
        alerts.append(make_alert(
            table,
            "orphan_table",
            "WARNING",
            "No lineage dependencies found",
        ))

    for cycle in graph.detect_cycles():
        alerts.append(make_alert(
            cycle[0],
            "lineage_cycle",
            "CRITICAL",
            " -> ".join(cycle),
        ))

    for error in parser_errors or []:
        alerts.append(make_alert(
            error["file"],
            "parser_error",
            "CRITICAL",
            error["error"],
        ))

    return alerts


def table_status(table, alerts):
    severities = {
        alert["severity"]
        for alert in alerts
        if alert["table"] == table
    }

    if "CRITICAL" in severities:
        return "RED"

    if "WARNING" in severities:
        return "YELLOW"

    return "GREEN"
