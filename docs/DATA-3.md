# DATA-3: Platform Health Console and Lineage Graph

## Objective

Implement a configuration-driven observability framework
for the wealth management data engineering platform.

The framework discovers transformation dependencies,
collects live table metrics, detects anomalies, maintains
persistent alerts and exposes platform health through a
command-line console.

## Architecture

SQL transformations and YAML lineage manifests
feed a unified dependency graph.

ClickHouse provides table inventory, row counts,
storage metadata and ingestion timestamps.

The anomaly engine evaluates observations against
configurable thresholds and historical snapshots.

SQLite persists metric history and alert lifecycle state.

The CLI exposes health classifications, lineage,
impact analysis and machine-readable reports.

## Core Coverage

- 10 Bronze tables
- 10 Silver tables
- 3 Gold tables
- 23 monitored tables
- 18 discovered dependency edges

Experimental SCD, CDC, staging and backup tables
are excluded from the core medallion graph.

## Components

| Module | Responsibility |
|---|---|
| graph.py | Dependency graph and impact analysis |
| sql_parser.py | SQL lineage extraction |
| yaml_parser.py | YAML lineage extraction |
| lineage.py | Unified graph discovery |
| metrics.py | Live ClickHouse metrics |
| anomalies.py | Configurable anomaly detection |
| store.py | Metric history and alert persistence |
| console.py | Platform health CLI |
| export_graph.py | Mermaid lineage documentation |

## Installation

    pip install -r requirements-health.txt

## Usage

Load the existing environment configuration and
ensure ClickHouse is running.

    set -a
    source .env
    set +a

Display live platform health:

    python -m platform_health.console

Display lineage:

    python -m platform_health.console --lineage

Analyze downstream impact:

    python -m platform_health.console --impact bronze_accounts

Export machine-readable results:

    python -m platform_health.console --json

Fail on critical anomalies:

    python -m platform_health.console --strict

Export the lineage graph:

    python -m platform_health.export_graph

## Health Classification

GREEN: No detected anomalies.

YELLOW: Warning conditions or unavailable metrics.

RED: Critical conditions, including missing tables,
empty tables, collection errors, critical freshness
violations or circular dependencies.

## Alert Lifecycle

Active alerts are deduplicated by table and rule.

Repeated observations update existing incidents
and increment occurrence counts.

Severity can escalate when thresholds are exceeded.

A subsequent complete observation without the
anomaly resolves the active incident.

Incomplete metric collection does not automatically
resolve existing incidents.

## Monitoring Policies

Thresholds are configured in:

    configs/health/thresholds.yaml

The initial thresholds are demonstration policies,
not contractual production service-level agreements.

Volume and storage changes are evaluated against
the previous successful observation.

## Verified Live Results

Initial monitoring discovered 23 tables and 18 edges,
with no missing tables, cycles or parser errors.

The collector observed 10,416 rows across all layers
and 165,891 bytes of known ClickHouse table storage.

The initial health console classified six tables as
GREEN, thirteen as YELLOW and four as RED.

Four Silver tables exceeded the configured critical
freshness threshold.

Repeated observations updated 27 active alerts
without creating duplicate incidents.

Strict monitoring correctly returned exit code 1
while critical freshness anomalies were present.

## Testing

    python -m unittest discover -s tests/platform_health -v

Tests cover SQL parsing, YAML validation, dependency
graphs, anomaly detection and alert lifecycle behavior.

## Limitations

- Bronze S3 storage sizes are not available through
  the current ClickHouse table metadata collector.
- Bronze and Gold ingestion timestamps are unavailable.
- Historical processing dates are not equivalent to
  ingestion timestamps.
- Row counts include records across all three layers,
  not unique business entities.
- Historical comparisons use the previous successful
  observation rather than a seasonal statistical model.
- SQLite persistence is designed for local monitoring
  with a single monitoring writer.
- Alerts are persisted locally; external notification
  delivery is not implemented.
- Monitoring runs on demand through the CLI.
- Generated YAML manifests must remain synchronized
  with Python transformation definitions.

## Related Documentation

- DATA-3-LINEAGE.md
- DATA-3-RUNBOOK.md
