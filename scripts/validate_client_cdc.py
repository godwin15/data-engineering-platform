import os
import clickhouse_connect

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.environ["CLICKHOUSE_PASSWORD"],
)

db = "wealth_management"

pending = client.query(f"""
SELECT count()
FROM {db}.client_cdc_events
WHERE event_id NOT IN (
    SELECT event_id
    FROM {db}.client_cdc_processed_events
)
""").result_rows[0][0]

duplicates = client.query(f"""
SELECT count() - uniqExact(tuple(organisation_id, client_id))
FROM {db}.silver_clients_current FINAL
""").result_rows[0][0]

total = client.query(
    f"SELECT count() FROM {db}.silver_clients_current FINAL"
).result_rows[0][0]

not_deleted = client.query(
    f"SELECT count() FROM {db}.silver_clients_current FINAL WHERE is_deleted = 0"
).result_rows[0][0]

print(f"Pending CDC events: {pending}")
print(f"Duplicate current client keys: {duplicates}")
print(f"Total current client keys: {total}")
print(f"Non-deleted clients: {not_deleted}")

assert pending == 0, "Some CDC events remain unprocessed"
assert duplicates == 0, "Duplicate current client keys detected"
assert total >= 0, "Invalid client count"
assert 0 <= not_deleted <= total, "Invalid non-deleted client count"

print("CDC DATA QUALITY PASSED")

# Verify the latest processed event for each client.
events = client.query(f"""
SELECT
    organisation_id,
    client_id,
    argMax(operation, tuple(event_time, event_id)) AS operation
FROM {db}.client_cdc_events
WHERE event_id IN (
    SELECT event_id FROM {db}.client_cdc_processed_events
)
GROUP BY organisation_id, client_id
""").result_rows

for org_id, client_id, operation in events:
    result = client.query(
        f"""
        SELECT is_deleted
        FROM {db}.silver_clients_current FINAL
        WHERE organisation_id = {{org:String}}
          AND client_id = {{cid:String}}
        """,
        parameters={"org": org_id, "cid": client_id},
    ).result_rows

    assert len(result) == 1, f"Missing client: {org_id}/{client_id}"

    expected_deleted = 1 if operation == "DELETE" else 0
    assert result[0][0] == expected_deleted, (
        f"Incorrect deletion state: {org_id}/{client_id}"
    )

print(f"CDC event-state validation passed for {len(events)} clients.")
