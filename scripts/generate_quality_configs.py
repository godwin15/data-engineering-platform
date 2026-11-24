from pathlib import Path
import yaml

CONFIG_DIR = Path("data_quality/config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

tables = {
    "clients": ("client_id", {}, ["client_name"], []),
    "accounts": ("account_id", {"client_id": "clients"}, [], []),
    "advisors": ("advisor_id", {}, [], []),
    "fees": ("fee_id", {"account_id": "accounts"}, [], []),
    "holdings": (
        "holding_id",
        {"portfolio_id": "portfolios", "security_id": "securities"},
        [],
        ["unit_price"],
    ),
    "portfolios": ("portfolio_id", {"account_id": "accounts"}, [], []),
    "securities": ("security_id", {}, [], []),
    "statements": ("statement_id", {"account_id": "accounts"}, [], []),
    "trades": (
        "trade_id",
        {"account_id": "accounts", "security_id": "securities"},
        [],
        ["price"],
    ),
    "transactions": (
        "transaction_id",
        {"account_id": "accounts"},
        [],
        [],
    ),
}

for entity, (key, references, required, ranges) in tables.items():
    table = f"silver_{entity}"
    path = CONFIG_DIR / f"{table}.yaml"
    primary_key = ["organisation_id", key, "processing_date"]

    config = {
        "table": table,
        "database": "wealth_management",
        "tenant_column": "organisation_id",
        "primary_key": primary_key,
        "checks": [],
    }

    if path.exists():
        config = yaml.safe_load(path.read_text())

    checks = config["checks"]

    def add(name, check_type, severity="ERROR", **params):
        if any(c["name"] == name for c in checks):
            return

        if any(
            c["type"] == check_type
            and all(c.get(k) == v for k, v in params.items())
            for c in checks
        ):
            return

        checks.append({
            "name": name,
            "type": check_type,
            **params,
            "severity": severity,
        })

    for column in ["organisation_id", key, *required, *references]:
        add(
            f"{column}_required",
            "null_check",
            column=column,
        )

    add(
        f"{entity}_key_unique",
        "unique_key",
        columns=primary_key,
    )

    for column, reference in references.items():
        add(
            f"{column}_tenant_integrity",
            "cross_tenant_check",
            entity_column=column,
            tenant_column="organisation_id",
            reference_table=f"silver_{reference}",
        )

    for column in ranges:
        add(
            f"{column}_nonnegative",
            "range_check",
            severity="WARNING",
            column=column,
            min=0,
        )

    path.write_text(yaml.safe_dump(config, sort_keys=False))
    print(f"{table}: {len(checks)} checks configured")

print(f"\nGenerated configurations for {len(tables)} tables.")
