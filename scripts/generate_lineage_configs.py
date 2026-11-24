import ast
from pathlib import Path

import yaml

from platform_health.sql_parser import extract_sql_lineage

DATABASE = "wealth_management"


def extract_dictionary(path, variable):
    tree = ast.parse(Path(path).read_text())

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == variable:
                        return ast.literal_eval(node.value)

    raise ValueError(f"{variable} not found in {path}")


def main():
    models = []

    silver = extract_dictionary(
        "scripts/run_silver_pipeline.py",
        "DATASETS",
    )

    for name in sorted(silver):
        models.append({
            "target": f"{DATABASE}.silver_{name}",
            "sources": [f"{DATABASE}.bronze_{name}"],
            "definition": "scripts/run_silver_pipeline.py",
        })

    gold = extract_dictionary(
        "scripts/run_gold_pipeline.py",
        "GOLD_MODELS",
    )

    for name, config in sorted(gold.items()):
        target = f"{DATABASE}.gold_{name}"

        sql = f"INSERT INTO {target} {config['sql']}"

        edges = extract_sql_lineage(sql)

        sources = sorted({
            source for source, destination in edges
            if destination == target
        })

        if not sources:
            raise ValueError(f"No sources discovered for {target}")

        models.append({
            "target": target,
            "sources": sources,
            "definition": "scripts/run_gold_pipeline.py",
        })

    path = Path("configs/lineage/python_models.yaml")
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        yaml.safe_dump({"models": models}, sort_keys=False)
    )

    print(f"Generated {len(models)} lineage models.")
    print(path.read_text())


if __name__ == "__main__":
    main()
