CREATE DATABASE IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.data_quality_metrics
(
    run_id String,
    pipeline_name String,
    table_name String,
    check_name String,
    metric_value Float64,
    expected_value Nullable(Float64),
    status LowCardinality(String),
    details String DEFAULT '',
    checked_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(checked_at)
ORDER BY (
    pipeline_name,
    table_name,
    check_name,
    checked_at,
    run_id
);

CREATE TABLE IF NOT EXISTS monitoring.pipeline_runs
(
    dag_id String,
    run_id String,
    status LowCardinality(String),
    started_at DateTime64(3),
    finished_at DateTime64(3),
    duration_seconds Float64,
    error_message String DEFAULT '',
    recorded_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(recorded_at)
ORDER BY (dag_id, run_id);
