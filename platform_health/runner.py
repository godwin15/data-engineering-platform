import json

from platform_health.lineage import build_lineage
from platform_health.metrics import MetricsCollector


def main():
    graph, errors = build_lineage()

    print("=== PLATFORM LINEAGE ===")
    print("Tables:", len(graph.nodes))
    print("Dependencies:", len(graph.edges))
    print("Cycles:", graph.detect_cycles())
    print("Orphans:", graph.orphan_tables())
    print("Parser errors:", errors)

    collector = MetricsCollector()

    try:
        metrics = collector.collect(graph.nodes)
    finally:
        collector.close()

    print("\n=== LIVE TABLE METRICS ===")

    for metric in metrics:
        print(json.dumps(metric, default=str))

    existing = [
        metric["table"]
        for metric in metrics
        if metric["exists"]
    ]

    print("\n=== PLATFORM SUMMARY ===")
    print("Monitored tables:", len(metrics))
    print("Missing tables:", graph.missing_tables(existing))
    print("Metric errors:", sum(
        bool(metric["errors"]) for metric in metrics
    ))

    print("Total observed rows:", sum(
        metric["rows"]
        for metric in metrics
        if metric["rows"] is not None
    ))

    print("Known storage bytes:", sum(
        metric["storage_bytes"]
        for metric in metrics
        if metric["storage_bytes"] is not None
    ))

    print("Unknown storage metrics:", sum(
        metric["storage_bytes"] is None
        for metric in metrics
    ))

    return int(bool(
        errors
        or graph.detect_cycles()
        or graph.missing_tables(existing)
        or any(metric["errors"] for metric in metrics)
    ))


if __name__ == "__main__":
    raise SystemExit(main())
