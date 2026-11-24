import argparse
import logging
import os
from collections import Counter
from pathlib import Path

from data_quality.schema import discover_configs
from data_quality.engine import QualityEngine
from data_quality.adapters.clickhouse import ClickHouseCountAdapter


DEFAULT_CONFIG = Path(__file__).resolve().parent / "config"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("data_quality")


def run_quality_checks(config_dir=DEFAULT_CONFIG):
    checks = discover_configs(config_dir)

    if not checks:
        raise ValueError("No quality checks discovered")

    adapter = ClickHouseCountAdapter(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )

    try:
        engine = QualityEngine(adapter)
        results = engine.execute(checks)

        for result in results:
            message = (
                f"{result.table}.{result.name}: "
                f"{result.status} "
                f"(violations={result.violation_count})"
            )

            if result.status == "ERROR":
                logger.error(message)
            elif result.status == "WARNING":
                logger.warning(message)
            else:
                logger.info(message)

        summary = Counter(result.status for result in results)
        failed = engine.should_fail_pipeline(results)

        print("\n=== DATA QUALITY SUMMARY ===")
        print(f"Tables: {len({c.table for c in checks})}")
        print(f"Checks: {len(results)}")
        print(f"Passed: {summary['PASS']}")
        print(f"Warnings: {summary['WARNING']}")
        print(f"Errors: {summary['ERROR']}")
        print(f"Pipeline failure: {failed}")

        return 1 if failed else 0

    finally:
        adapter.close()


def main():
    parser = argparse.ArgumentParser(
        description="Execute configuration-driven data quality checks"
    )

    parser.add_argument(
        "--config-dir",
        default=str(DEFAULT_CONFIG),
    )

    args = parser.parse_args()
    return run_quality_checks(args.config_dir)


if __name__ == "__main__":
    raise SystemExit(main())
