from pathlib import Path
import re

import yaml


IDENTIFIER = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$"
)


def validate_table(value):
    if not isinstance(value, str):
        raise ValueError("Table name must be a string")

    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid qualified table: {value}")

    return value


def extract_yaml_lineage(path):
    config = yaml.safe_load(Path(path).read_text())

    if not isinstance(config, dict):
        raise ValueError("Expected a YAML mapping")

    models = config.get("models")

    if not isinstance(models, list) or not models:
        raise ValueError("Expected nonempty models list")

    edges = set()

    for model in models:
        target = validate_table(model["target"])
        sources = model["sources"]

        if not isinstance(sources, list) or not sources:
            raise ValueError(f"No sources for {target}")

        for source in sources:
            edges.add((validate_table(source), target))

    return sorted(edges)


def discover_yaml_lineage(directory):
    edges = set()
    errors = []

    paths = [
        *Path(directory).rglob("*.yaml"),
        *Path(directory).rglob("*.yml"),
    ]

    for path in sorted(paths):
        try:
            edges.update(extract_yaml_lineage(path))
        except Exception as exc:
            errors.append({
                "file": str(path),
                "error": str(exc),
            })

    return sorted(edges), errors
