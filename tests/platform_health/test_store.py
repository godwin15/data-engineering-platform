import unittest

from platform_health.store import HealthStore


class TestHealthStore(unittest.TestCase):

    def setUp(self):
        self.store = HealthStore(":memory:")

        self.alert = {
            "table": "db.silver_clients",
            "rule": "stale_data",
            "severity": "WARNING",
            "message": "Data is stale",
        }

    def tearDown(self):
        self.store.close()

    def test_new_alert(self):
        result = self.store.sync_alerts([self.alert])
        self.assertEqual(result["new"], 1)

    def test_deduplication(self):
        self.store.sync_alerts([self.alert])
        result = self.store.sync_alerts([self.alert])

        self.assertEqual(result["new"], 0)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(len(self.store.active_alerts()), 1)

    def test_occurrence_tracking(self):
        self.store.sync_alerts([self.alert])
        self.store.sync_alerts([self.alert])

        self.assertEqual(
            self.store.active_alerts()[0]["occurrences"], 2
        )

    def test_escalation(self):
        self.store.sync_alerts([self.alert])

        critical = dict(self.alert, severity="CRITICAL")
        result = self.store.sync_alerts([critical])

        self.assertEqual(result["escalated"], 1)
        self.assertEqual(
            self.store.active_alerts()[0]["severity"],
            "CRITICAL",
        )

    def test_resolution(self):
        self.store.sync_alerts([self.alert])
        result = self.store.sync_alerts([])

        self.assertEqual(result["resolved"], 1)
        self.assertEqual(self.store.active_alerts(), [])

    def test_reopened_incident(self):
        self.store.sync_alerts([self.alert])
        self.store.sync_alerts([])
        result = self.store.sync_alerts([self.alert])

        self.assertEqual(result["new"], 1)

    def test_metric_history(self):
        metric = {
            "table": "db.silver_clients",
            "rows": 100,
            "storage_bytes": 1000,
            "exists": True,
            "errors": [],
        }

        self.store.save_metrics([metric])

        self.assertEqual(
            self.store.latest_metrics()[metric["table"]]["rows"],
            100,
        )

    def test_latest_metric_snapshot(self):
        metric = {
            "table": "db.silver_clients",
            "rows": 100,
            "exists": True,
            "errors": [],
        }

        self.store.save_metrics([metric])
        self.store.save_metrics([dict(metric, rows=200)])

        self.assertEqual(
            self.store.latest_metrics()[metric["table"]]["rows"],
            200,
        )


if __name__ == "__main__":
    unittest.main()
