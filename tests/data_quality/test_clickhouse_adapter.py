import unittest
from unittest.mock import Mock, patch

from data_quality.schema import QualityCheck
from data_quality.adapters.clickhouse import ClickHouseCountAdapter


class TestClickHouseAdapter(unittest.TestCase):

    def setUp(self):
        patcher = patch(
            "data_quality.adapters.clickhouse.clickhouse_connect.get_client"
        )
        self.addCleanup(patcher.stop)
        mock_get_client = patcher.start()

        self.client = Mock()
        mock_get_client.return_value = self.client
        self.client.query.return_value.result_rows = [(0,)]

        self.adapter = ClickHouseCountAdapter()

    def make_check(self, check_type, parameters):
        return QualityCheck(
            database="wealth_management",
            table="silver_clients",
            name="test_check",
            check_type=check_type,
            severity="ERROR",
            parameters=parameters,
        )

    def test_null_check(self):
        check = self.make_check(
            "null_check", {"column": "organisation_id"}
        )
        self.assertEqual(self.adapter.count_violations(check), 0)

        sql = self.client.query.call_args.args[0]
        self.assertIn("organisation_id IS NULL", sql)
        self.assertIn("toString(organisation_id) = ''", sql)

    def test_unique_key(self):
        check = self.make_check(
            "unique_key",
            {"columns": ["organisation_id", "client_id", "processing_date"]},
        )
        self.adapter.count_violations(check)

        sql = self.client.query.call_args.args[0]
        self.assertIn(
            "GROUP BY organisation_id, client_id, processing_date", sql
        )
        self.assertIn("HAVING count() > 1", sql)

    def test_row_count_reconciliation(self):
        check = self.make_check(
            "row_count_reconciliation", {"expected_count": 210}
        )
        self.adapter.count_violations(check)

        sql = self.client.query.call_args.args[0]
        self.assertIn("abs(toInt64(count()) - 210)", sql)

    def test_cross_tenant_check(self):
        check = self.make_check(
            "cross_tenant_check",
            {
                "entity_column": "client_id",
                "tenant_column": "organisation_id",
                "reference_table": "silver_clients",
            },
        )
        self.adapter.count_violations(check)

        sql = self.client.query.call_args.args[0]
        self.assertIn("NOT EXISTS", sql)
        self.assertIn(
            "c.organisation_id = a.organisation_id", sql
        )
        self.assertIn("c.client_id = a.client_id", sql)
        self.assertIn("c.processing_date = a.processing_date", sql)

    def test_invalid_identifier_rejected(self):
        check = self.make_check(
            "null_check", {"column": "id; DROP TABLE clients"}
        )
        with self.assertRaises(ValueError):
            self.adapter.count_violations(check)

        self.client.query.assert_not_called()

    def test_range_check(self):
        check = self.make_check(
            "range_check",
            {"column": "balance", "min": 0, "max": 10000},
        )
        self.adapter.count_violations(check)

        sql = self.client.query.call_args.args[0]
        self.assertIn("balance < 0", sql)
        self.assertIn("balance > 10000", sql)

    def test_range_check_requires_bound(self):
        check = self.make_check(
            "range_check", {"column": "balance"}
        )
        with self.assertRaises(ValueError):
            self.adapter.count_violations(check)

        self.client.query.assert_not_called()

    def test_range_check_rejects_invalid_bounds(self):
        check = self.make_check(
            "range_check",
            {"column": "balance", "min": 100, "max": 0},
        )
        with self.assertRaises(ValueError):
            self.adapter.count_violations(check)

        self.client.query.assert_not_called()

    def test_returns_violation_count(self):
        self.client.query.return_value.result_rows = [(3,)]
        check = self.make_check(
            "null_check", {"column": "organisation_id"}
        )
        self.assertEqual(self.adapter.count_violations(check), 3)

    def test_close(self):
        self.adapter.close()
        self.client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
