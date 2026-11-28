import sqlglot
from sqlglot import exp


TENANT_COLUMN = "organisation_id"


def validate_gold_sql(sql):
    statements = sqlglot.parse(sql, read="clickhouse")

    if len(statements) != 1:
        raise ValueError("Expected exactly one SQL statement")

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise ValueError("Gold model must be a SELECT query")

    errors = []

    for select in tree.find_all(exp.Select):
        group = select.args.get("group")

        aggregates = [
            node for node in select.find_all(exp.AggFunc)
            if node.find_ancestor(exp.Select) is select
        ]

        if aggregates or group is not None:
            grouped_columns = {
                expression.name.lower()
                for expression in group.expressions
                if isinstance(expression, exp.Column)
            } if group is not None else set()

            if TENANT_COLUMN not in grouped_columns:
                errors.append(
                    "Aggregation missing organisation_id in GROUP BY"
                )

        for join in select.args.get("joins", []):
            condition = join.args.get("on")

            if condition is None:
                errors.append("JOIN missing explicit tenant condition")
                continue

            predicates = []

            def flatten_and(expression):
                if isinstance(expression, exp.Paren):
                    flatten_and(expression.this)
                elif isinstance(expression, exp.And):
                    flatten_and(expression.this)
                    flatten_and(expression.expression)
                else:
                    predicates.append(expression)

            flatten_and(condition)

            tenant_join = any(
                isinstance(predicate, exp.EQ)
                and isinstance(predicate.this, exp.Column)
                and isinstance(predicate.expression, exp.Column)
                and predicate.this.name.lower() == TENANT_COLUMN
                and predicate.expression.name.lower() == TENANT_COLUMN
                and predicate.this.table
                and predicate.expression.table
                and predicate.this.table != predicate.expression.table
                for predicate in predicates
            )

            if not tenant_join:
                errors.append(
                    "JOIN missing organisation_id equality"
                )

    if errors:
        raise ValueError("; ".join(errors))

    return True
