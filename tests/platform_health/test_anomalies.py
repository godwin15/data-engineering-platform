import unittest

from platform_health.graph import LineageGraph
from platform_health.anomalies import (
    detect_anomalies,
    load_thresholds,
    table_status,
)


class TestAnomalies(unittest.TestCase):

    def setUp(self):
        self.config = load_thresholds()
        self.graph = LineageGraph()
        self.graph.add_dependency("db.bronze", "db.silver")

        self.metric = {
            "table": "db.silver",
            "exists": True,
            "rows": 100,
            "storage_bytes": 1000,
            "freshness_hours": 1,
            "errors": [],
        }

    def evaluate(self, previous=None, **changes):
        metric = dict(self.metric, **changes)

        return detect_anomalies(
            [metric],
            self.graph,
            previous or {},
            self.config,
        )

    def test_healthy_table(self):
        self.assertEqual(self.evaluate(), [])

    def test_freshness_warning(self):
        alerts = self.evaluate(freshness_hours=30)
        self.assertEqual(alerts[0]["severity"], "WARNING")

    def test_freshness_critical(self):
        alerts = self.evaluate(freshness_hours=72)
        self.assertEqual(alerts[0]["severity"], "CRITICAL")

    def test_unknown_freshness(self):
        alerts = self.evaluate(freshness_hours=None)
        self.assertEqual(alerts[0]["rule"], "unknown_freshness")

    def test_missing_table(self):
        alerts = self.evaluate(exists=False)
        self.assertEqual(alerts[0]["rule"], "missing_table")

    def test_empty_table(self):
        alerts = self.evaluate(rows=0)
        self.assertEqual(alerts[0]["rule"], "empty_table")

    def test_volume_warning(self):
        alerts = self.evaluate(
            {"db.silver": {"rows": 100}},
            rows=125,
        )
        self.assertEqual(alerts[0]["severity"], "WARNING")

    def test_volume_critical(self):
        alerts = self.evaluate(
            {"db.silver": {"rows": 100}},
            rows=40,
        )
        self.assertEqual(alerts[0]["severity"], "CRITICAL")

    def test_storage_growth(self):
        alerts = self.evaluate(
            {"db.silver": {"storage_bytes": 1000}},
            storage_bytes=2500,
        )
        self.assertEqual(alerts[0]["rule"], "storage_growth")
        self.assertEqual(alerts[0]["severity"], "CRITICAL")

    def test_unknown_storage(self):
        alerts = self.evaluate(storage_bytes=None)
        self.assertEqual(alerts[0]["rule"], "unknown_storage")

    def test_collection_error(self):
        alerts = self.evaluate(errors=["Connection failed"])
        self.assertEqual(alerts[0]["rule"], "collection_error")

    def test_red_status(self):
        alerts = self.evaluate(freshness_hours=72)
        self.assertEqual(
            table_status("db.silver", alerts), "RED"
        )

    def test_yellow_status(self):
        alerts = self.evaluate(freshness_hours=30)
        self.assertEqual(
            table_status("db.silver", alerts), "YELLOW"
        )

    def test_green_status(self):
        self.assertEqual(
            table_status("db.silver", []), "GREEN"
        )

    def test_cycle_alert(self):
        self.graph.add_dependency("db.silver", "db.bronze")
        alerts = self.evaluate()

        self.assertTrue(any(
            a["rule"] == "lineage_cycle" for a in alerts
        ))


if __name__ == "__main__":
    unittest.main()
