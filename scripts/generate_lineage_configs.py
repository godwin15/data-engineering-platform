from pathlib import Path

import yaml

from scripts.pipeline_config import load_models
from platform_health.sql_parser import extract_sql_lineage


def main():
    models = []

    silver = load_models("silver_python.yaml")
    gold = load_models("gold.yaml")

    for name in silver:
        models.append({
            "target": f"wealth_management.silver_{name}",
            "sources": [
                f"wealth_management.bronze_{name}"
            ],
            "definition": "configs/pipelines/silver_python.yaml",
        })

    for name, config in gold.items():
        target = f"wealth_management.gold_{name}"

        edges = extract_sql_lineage(
            f"INSERT INTO {target} {config['sql']}"
        )

        sources = sorted({
            source
            for source, destination in edges
            if destination == target
        })

        if not sources:
            raise ValueError(f"No dependencies found for {target}")

        models.append({
            "target": target,
            "sources": sources,
            "definition": "configs/pipelines/gold.yaml",
        })

    output = Path("configs/lineage/python_models.yaml")
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        yaml.safe_dump({"models": models}, sort_keys=False)
    )

    print(f"Generated lineage for {len(models)} models.")


if __name__ == "__main__":
    main()
