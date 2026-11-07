import os
from datetime import datetime

import clickhouse_connect

DB = "wealth_management"

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.environ["CLICKHOUSE_PASSWORD"],
)

FIELDS = [
    "client_name",
    "email",
    "country",
    "risk_profile",
    "account_status",
]


def fetch_current(org_id, client_id):
    result = client.query(
        f"""
        SELECT
            client_name, email, country, risk_profile,
            account_status, is_deleted, version
        FROM {DB}.silver_clients_current FINAL
        WHERE organisation_id = {{org:String}}
          AND client_id = {{cid:String}}
        """,
        parameters={"org": org_id, "cid": client_id},
    )
    return dict(zip(FIELDS + ["is_deleted", "version"], result.result_rows[0])) if result.result_rows else None


def process_events():
    events = client.query(
        f"""
        SELECT
            event_id, organisation_id, client_id, operation,
            client_name, email, country, risk_profile,
            account_status, event_time, processing_date
        FROM {DB}.client_cdc_events
        ORDER BY event_time, event_id
        """
    ).named_results()

    processed = set(
        row[0]
        for row in client.query(
            f"SELECT DISTINCT event_id FROM {DB}.client_cdc_processed_events"
        ).result_rows
    )

    applied = 0

    for event in events:
        if event["event_id"] in processed:
            continue

        org_id = event["organisation_id"]
        client_id = event["client_id"]
        operation = event["operation"].upper()
        existing = fetch_current(org_id, client_id)

        # Millisecond Unix timestamp as the version.
        version = int(event["event_time"].timestamp() * 1000)

        if existing and version <= existing["version"]:
            client.insert(
                f"{DB}.client_cdc_processed_events",
                [[event["event_id"]]],
                column_names=["event_id"],
            )
            processed.add(event["event_id"])
            print(f"Recorded stale/replayed event: {event['event_id']}")
            continue

        if operation not in {"INSERT", "UPDATE", "DELETE"}:
            raise ValueError(f"Unknown operation: {operation}")

        if operation == "INSERT" and existing and not existing["is_deleted"]:
            raise ValueError(f"Client already exists: {org_id}/{client_id}")

        if operation in {"UPDATE", "DELETE"} and not existing:
            raise ValueError(f"Client not found: {org_id}/{client_id}")

        if operation == "UPDATE" and existing["is_deleted"]:
            raise ValueError(f"Cannot update deleted client: {org_id}/{client_id}")

        if operation == "DELETE":
            values = {field: existing[field] for field in FIELDS}
            is_deleted = 1
        else:
            values = {
                field: (
                    event[field]
                    if event[field] is not None
                    else existing[field] if existing else None
                )
                for field in FIELDS
            }
            is_deleted = 0

        client.insert(
            f"{DB}.silver_clients_current",
            [[
                org_id,
                client_id,
                *(values[field] for field in FIELDS),
                event["processing_date"],
                datetime.now(),
                is_deleted,
                version,
            ]],
            column_names=[
                "organisation_id",
                "client_id",
                *FIELDS,
                "processing_date",
                "ingested_at",
                "is_deleted",
                "version",
            ],
        )

        client.insert(
            f"{DB}.client_cdc_processed_events",
            [[event["event_id"]]],
            column_names=["event_id"],
        )

        processed.add(event["event_id"])
        applied += 1
        print(f"Applied {operation}: {org_id}/{client_id}")

    print(f"Completed. Applied {applied} events.")


if __name__ == "__main__":
    process_events()
