from pathlib import Path

from platform_health.lineage import build_lineage


def export_mermaid(path="docs/DATA-3-LINEAGE.md"):
    graph, errors = build_lineage()

    if errors:
        raise RuntimeError(f"Lineage parser errors: {errors}")

    lines = [
        "# Platform Data Lineage",
        "",
        "Generated from SQL and YAML transformation definitions.",
        "",
        f"- Tables: {len(graph.nodes)}",
        f"- Dependencies: {len(graph.edges)}",
        f"- Cycles: {len(graph.detect_cycles())}",
        "",
        "```mermaid",
        "flowchart LR",
    ]

    identifiers = {
        table: f"T{i}"
        for i, table in enumerate(sorted(graph.nodes))
    }

    for layer in ("bronze", "silver", "gold"):
        lines.append(
            f'    subgraph {layer.upper()}["{layer.title()} Layer"]'
        )

        for table in sorted(graph.nodes):
            name = table.split(".")[-1]

            if name.startswith(f"{layer}_"):
                lines.append(
                    f'        {identifiers[table]}["{name}"]'
                )

        lines.append("    end")

    for source, target in sorted(graph.edges):
        lines.append(
            f"    {identifiers[source]} --> {identifiers[target]}"
        )

    lines.append("```")
    lines.append("")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))

    print(f"Lineage graph exported to {output}")


if __name__ == "__main__":
    export_mermaid()
