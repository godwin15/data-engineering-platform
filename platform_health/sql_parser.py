from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope


def table_name(table, default_database="wealth_management"):
    database = table.db or default_database
    return f"{database}.{table.name}"


def extract_sql_lineage(sql, default_database="wealth_management"):
    dependencies = set()

    statements = sqlglot.parse(sql, read="clickhouse")

    for statement in statements:
        if statement is None:
            continue

        if not isinstance(statement, (exp.Insert, exp.Create)):
            continue

        target = statement.this

        if isinstance(target, exp.Schema):
            target = target.this

        if not isinstance(target, exp.Table):
            continue

        query = statement.expression

        if query is None:
            continue

        target_name = table_name(target, default_database)

        for scope in traverse_scope(query):
            for source in scope.sources.values():
                if isinstance(source, exp.Table):
                    source_name = table_name(
                        source, default_database
                    )

                    dependencies.add(
                        (source_name, target_name)
                    )

    return sorted(dependencies)


def discover_sql_lineage(directory):
    dependencies = set()
    errors = []

    for path in sorted(Path(directory).rglob("*.sql")):
        try:
            dependencies.update(
                extract_sql_lineage(path.read_text())
            )
        except Exception as exc:
            errors.append({
                "file": str(path),
                "error": str(exc),
            })

    return sorted(dependencies), errors
