import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class HealthStore:

    def __init__(self, path="runtime/platform_health.db"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row

        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS metric_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observed_at TEXT NOT NULL,
                table_name TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_metric_table
            ON metric_history(table_name, id);

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                rule TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                occurrences INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                resolved_at TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_active_alert
            ON alerts(table_name, rule)
            WHERE status = 'ACTIVE';
        """)

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def latest_metrics(self):
        rows = self.connection.execute("""
            SELECT table_name, payload
            FROM metric_history
            WHERE id IN (
                SELECT MAX(id)
                FROM metric_history
                GROUP BY table_name
            )
        """).fetchall()

        return {
            row["table_name"]: json.loads(row["payload"])
            for row in rows
        }

    def save_metrics(self, metrics):
        timestamp = self.now()

        with self.connection:
            self.connection.executemany("""
                INSERT INTO metric_history
                (observed_at, table_name, payload)
                VALUES (?, ?, ?)
            """, [
                (
                    timestamp,
                    metric["table"],
                    json.dumps(metric, default=str),
                )
                for metric in metrics
                if metric["exists"] and not metric["errors"]
            ])

    def sync_alerts(self, alerts):
        timestamp = self.now()

        active = {
            (row["table_name"], row["rule"]): dict(row)
            for row in self.connection.execute("""
                SELECT * FROM alerts
                WHERE status = 'ACTIVE'
            """)
        }

        current = set()

        summary = {
            "new": 0,
            "updated": 0,
            "escalated": 0,
            "resolved": 0,
        }

        with self.connection:
            for alert in alerts:
                key = (alert["table"], alert["rule"])

                if key in current:
                    continue

                current.add(key)

                if key in active:
                    existing = active[key]

                    self.connection.execute("""
                        UPDATE alerts
                        SET severity = ?,
                            message = ?,
                            last_seen = ?,
                            occurrences = occurrences + 1
                        WHERE id = ?
                    """, (
                        alert["severity"],
                        alert["message"],
                        timestamp,
                        existing["id"],
                    ))

                    summary["updated"] += 1

                    if (
                        existing["severity"] == "WARNING"
                        and alert["severity"] == "CRITICAL"
                    ):
                        summary["escalated"] += 1

                else:
                    self.connection.execute("""
                        INSERT INTO alerts (
                            table_name, rule, severity,
                            message, first_seen, last_seen
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        alert["table"],
                        alert["rule"],
                        alert["severity"],
                        alert["message"],
                        timestamp,
                        timestamp,
                    ))

                    summary["new"] += 1

            for key, existing in active.items():
                if key not in current:
                    self.connection.execute("""
                        UPDATE alerts
                        SET status = 'RESOLVED',
                            resolved_at = ?
                        WHERE id = ?
                    """, (
                        timestamp,
                        existing["id"],
                    ))

                    summary["resolved"] += 1

        return summary

    def active_alerts(self):
        return [
            dict(row)
            for row in self.connection.execute("""
                SELECT * FROM alerts
                WHERE status = 'ACTIVE'
                ORDER BY
                    CASE severity
                        WHEN 'CRITICAL' THEN 0
                        ELSE 1
                    END,
                    table_name
            """)
        ]

    def close(self):
        self.connection.close()
