import argparse
import json
import sys
from collections import Counter

from platform_health.lineage import build_lineage
from platform_health.metrics import MetricsCollector
from platform_health.anomalies import (
    load_thresholds,
    detect_anomalies,
    table_status,
)
from platform_health.store import HealthStore


COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
}


def colored(status):
    if not sys.stdout.isatty():
        return status

    return f"{COLORS[status]}{status}\033[0m"


def display(value):
    return "N/A" if value is None else str(value)


def print_lineage(graph):
    print("\n=== TABLE LINEAGE ===")

    for source, target in sorted(graph.edges):
        print(
            f"{source.split('.')[-1]}"
            f" -> {target.split('.')[-1]}"
        )


def print_impact(graph, table):
    if "." not in table:
        table = f"wealth_management.{table}"

    if table not in graph.nodes:
        raise ValueError(f"Unknown table: {table}")

    print(f"\n=== IMPACT ANALYSIS: {table} ===")

    print("Direct upstream:")
    for item in graph.upstream(table):
        print(f"  {item}")

    print("All upstream dependencies:")
    for item in graph.ancestors(table):
        print(f"  {item}")

    print("Potentially impacted downstream tables:")
    for item in graph.descendants(table):
        print(f"  {item}")


def main():
    parser = argparse.ArgumentParser(
        description="Data Engineering Platform Health Console"
    )

    parser.add_argument("--lineage", action="store_true")
    parser.add_argument("--impact")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--state",
        default="runtime/platform_health.db",
    )

    args = parser.parse_args()

    graph, errors = build_lineage()

    if args.impact:
        print_impact(graph, args.impact)
        return 0

    if args.lineage:
        print_lineage(graph)
        print(f"\nTables: {len(graph.nodes)}")
        print(f"Dependencies: {len(graph.edges)}")
        print(f"Cycles: {graph.detect_cycles()}")
        print(f"Parser errors: {errors}")
        return int(bool(errors or graph.detect_cycles()))

    if errors:
        print(json.dumps({
            "status": "RED",
            "parser_errors": errors,
        }, indent=2))
        return 1

    config = load_thresholds()
    collector = MetricsCollector()
    store = HealthStore(args.state)

    try:
        metrics = collector.collect(graph.nodes)
        previous = store.latest_metrics()

        alerts = detect_anomalies(
            metrics,
            graph,
            previous,
            config,
            errors,
        )

        # An incomplete observation must not resolve
        # previously active incidents.
        complete = bool(metrics) and not any(
            metric["errors"] and metric["exists"]
            for metric in metrics
        )

        if complete:
            changes = store.sync_alerts(alerts)
            store.save_metrics(metrics)
        else:
            changes = {"skipped": "Incomplete metric collection"}

        active = store.active_alerts()

        for metric in metrics:
            metric["status"] = table_status(
                metric["table"], alerts
            )

        counts = Counter(
            metric["status"] for metric in metrics
        )

        critical = any(
            alert["severity"] == "CRITICAL"
            for alert in alerts
        )

        overall = (
            "RED" if critical
            else "YELLOW" if alerts
            else "GREEN"
        )

        if args.json:
            print(json.dumps({
                "status": overall,
                "lineage": graph.to_dict(),
                "metrics": metrics,
                "current_anomalies": alerts,
                "active_alerts": active,
                "alert_changes": changes,
            }, indent=2, default=str))

        else:
            print("=" * 86)
            print("        DATA ENGINEERING PLATFORM - HEALTH CONSOLE")
            print("=" * 86)

            print(f"Overall status: {colored(overall)}")
            print(f"Tables monitored: {len(metrics)}")
            print(f"Lineage edges: {len(graph.edges)}")

            print(
                f"GREEN: {counts['GREEN']} | "
                f"YELLOW: {counts['YELLOW']} | "
                f"RED: {counts['RED']}"
            )

            print("\n=== TABLE HEALTH ===")

            print(
                f"{'TABLE':<28}"
                f"{'ROWS':>8}"
                f"{'BYTES':>12}"
                f"{'AGE (H)':>12}"
                f"  STATUS"
            )

            print("-" * 86)

            for metric in metrics:
                name = metric["table"].split(".")[-1]

                print(
                    f"{name:<28}"
                    f"{display(metric['rows']):>8}"
                    f"{display(metric['storage_bytes']):>12}"
                    f"{display(metric['freshness_hours']):>12}"
                    f"  {colored(metric['status'])}"
                )

            print("\n=== CURRENT ANOMALIES ===")

            for alert in alerts:
                print(
                    f"[{alert['severity']}] "
                    f"{alert['table'].split('.')[-1]} | "
                    f"{alert['rule']} | "
                    f"{alert['message']}"
                )

            print("\n=== ALERT LIFECYCLE ===")

            for key, value in changes.items():
                print(f"{key.title()}: {value}")

            print(f"Persisted active alerts: {len(active)}")
            print(
                f"Tables with historical baseline: "
                f"{len(previous)}"
            )

        return int(args.strict and critical)

    finally:
        collector.close()
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
