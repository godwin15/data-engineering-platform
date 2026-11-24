from dataclasses import dataclass
from pathlib import Path
import re

import yaml


SUPPORTED_CHECKS = {
    "null_check",
    "unique_key",
    "range_check",
    "cross_tenant_check",
    "row_count_reconciliation",
}

SUPPORTED_SEVERITIES = {"ERROR", "WARNING"}

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class QualityCheck:
    database: str
    table: str
    name: str
    check_type: str
    severity: str
    parameters: dict


def validate_identifier(value, field):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {field}: {value!r}")
    return value


def load_config(path):
    path = Path(path)

    with path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(f"{path}: configuration must be a mapping")

    database = validate_identifier(
        config.get("database"), "database"
    )
    table = validate_identifier(config.get("table"), "table")

    checks = config.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError(f"{path}: checks must be a nonempty list")

    parsed = []
    seen_names = set()

    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise ValueError(f"{path}: check {index} must be a mapping")

        name = validate_identifier(check.get("name"), "check name")
        check_type = check.get("type")
        severity = check.get("severity", "ERROR")

        if name in seen_names:
            raise ValueError(f"{path}: duplicate check name {name}")

        if check_type not in SUPPORTED_CHECKS:
            raise ValueError(
                f"{path}: unsupported check type {check_type}"
            )

        if severity not in SUPPORTED_SEVERITIES:
            raise ValueError(
                f"{path}: invalid severity {severity}"
            )

        parameters = {
            key: value
            for key, value in check.items()
            if key not in {"name", "type", "severity"}
        }

        for key in ("column", "entity_column", "tenant_column",
                    "reference_table"):
            if key in parameters:
                validate_identifier(parameters[key], key)

        if "columns" in parameters:
            columns = parameters["columns"]
            if not isinstance(columns, list) or not columns:
                raise ValueError(f"{path}: columns must be a nonempty list")
            for column in columns:
                validate_identifier(column, "column")

        parsed.append(
            QualityCheck(
                database=database,
                table=table,
                name=name,
                check_type=check_type,
                severity=severity,
                parameters=parameters,
            )
        )
        seen_names.add(name)

    return parsed


def discover_configs(directory):
    directory = Path(directory)
    files = sorted(directory.rglob("*.yaml"))

    if not files:
        raise ValueError(f"No YAML configurations found in {directory}")

    checks = []
    for file in files:
        checks.extend(load_config(file))

    return checks
