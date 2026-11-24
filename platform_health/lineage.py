from platform_health.graph import LineageGraph
from platform_health.sql_parser import discover_sql_lineage
from platform_health.yaml_parser import discover_yaml_lineage


def build_lineage(
    sql_dir="sql",
    yaml_dir="configs/lineage",
    core_only=True,
):
    sql_edges, sql_errors = discover_sql_lineage(sql_dir)
    yaml_edges, yaml_errors = discover_yaml_lineage(yaml_dir)

    graph = LineageGraph()

    experimental_suffixes = (
        "_history",
        "_current",
        "_scd_test",
        "_backup",
        "_staging",
    )

    def included(table):
        name = table.split(".")[-1]

        return (
            name.startswith(("bronze_", "silver_", "gold_"))
            and not name.endswith(experimental_suffixes)
        )

    for source, target in sql_edges + yaml_edges:
        if core_only:
            if not included(source) or not included(target):
                continue

        graph.add_dependency(source, target)

    errors = sql_errors + yaml_errors

    if not graph.nodes:
        errors.append({
            "file": "lineage",
            "error": "No lineage tables discovered",
        })

    return graph, errors
