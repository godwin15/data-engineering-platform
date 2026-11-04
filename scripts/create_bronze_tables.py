import os
from pathlib import Path

import clickhouse_connect

SQL_FILE = Path("sql/bronze/create_bronze_tables.sql")

access_key = os.environ["MINIO_ROOT_USER"]
secret_key = os.environ["MINIO_ROOT_PASSWORD"]

sql = SQL_FILE.read_text()

def sql_escape(value):
    return value.replace("\\", "\\\\").replace("'", "\\'")

sql = sql.replace(
    "__MINIO_ACCESS_KEY__",
    sql_escape(access_key)
).replace(
    "__MINIO_SECRET_KEY__",
    sql_escape(secret_key)
)

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.environ["CLICKHOUSE_USER"],
    password=os.environ["CLICKHOUSE_PASSWORD"],
)

statements = [
    statement.strip()
    for statement in sql.split(";")
    if statement.strip()
]

for statement in statements:
    client.command(statement)

print(f"Successfully executed {len(statements)} Bronze SQL statements.")
