from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "pipelines"

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ALLOWED_TYPES = {
    "String",
    "Nullable(String)",
    "Int64",
    "Nullable(Int64)",
    "Float64",
    "Nullable(Float64)",
    "Date",
    "DateTime",
}


def validate_identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid identifier: {value!r}")
    return value


def load_models(filename):
    path = CONFIG_DIR / filename
    config = yaml.safe_load(path.read_text())

    if not isinstance(config, dict):
        raise ValueError(f"{path}: expected a mapping")

    models = config.get("models")

    if not isinstance(models, dict) or not models:
        raise ValueError(f"{path}: no models defined")

    for name, model in models.items():
        validate_identifier(name)

        if not isinstance(model, dict):
            raise ValueError(f"{name}: invalid model")

        if filename == "silver_python.yaml":
            key = validate_identifier(model.get("key"))
            columns = model.get("columns")

            if not isinstance(columns, dict) or key not in columns:
                raise ValueError(f"{name}: invalid columns or key")

            for column, dtype in columns.items():
                validate_identifier(column)

                if dtype not in ALLOWED_TYPES:
                    raise ValueError(
                        f"{name}: unsupported type {dtype}"
                    )

        elif filename == "silver_sql.yaml":
            key = model.get("key")

            if not isinstance(key, str) or not __import__("re").fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*", key
            ):
                raise ValueError(
                    f"Invalid Silver SQL business key: {name}"
                )

            target = validate_identifier(model.get("target"))

            if target != f"silver_{name}":
                raise ValueError(f"{name}: incorrect target")

            sql_path = (ROOT / model["sql_file"]).resolve()

            if not sql_path.is_relative_to(ROOT / "sql" / "silver"):
                raise ValueError(f"{name}: invalid SQL path")

            if not sql_path.is_file():
                raise ValueError(f"{name}: SQL file not found")

        elif filename == "gold.yaml":
            keys = model.get("key", "").split(",")

            for key in keys:
                validate_identifier(key.strip())

            sql = model.get("sql")

            if not isinstance(sql, str):
                raise ValueError(f"{name}: SQL is required")

            if not sql.strip().upper().startswith("SELECT"):
                raise ValueError(f"{name}: expected SELECT query")

        else:
            raise ValueError(f"Unsupported configuration: {filename}")

    return models


if __name__ == "__main__":
    total = 0

    for filename in (
        "silver_python.yaml",
        "silver_sql.yaml",
        "gold.yaml",
    ):
        models = load_models(filename)
        total += len(models)
        print(f"PASS: {filename}: {len(models)} models")

    print(f"Validated {total} pipeline models.")
