import os
import unittest

from data_quality.engine import QualityEngine
from data_quality.adapters.clickhouse import ClickHouseCountAdapter
from run_quality_checks import checks


class TestCorruptionScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.adapter = ClickHouseCountAdapter(
            password=os.environ["CLICKHOUSE_PASSWORD"]
        )
        cls.engine = QualityEngine(cls.adapter)
        cls.client = cls.adapter.client

    @classmethod
    def tearDownClass(cls):
        cls.adapter.close()

    def execute(self):
        results = self.engine.execute(checks)
        return (
            {result.name: result for result in results},
            self.engine.should_fail_pipeline(results),
        )

    def assert_clean(self):
        results, failed = self.execute()
        self.assertFalse(failed)

        for result in results.values():
            self.assertEqual(result.status, "PASS")
            self.assertEqual(result.violation_count, 0)

    def run_scenario(
        self,
        insert_sql,
        cleanup_sql,
        check_name,
        expected_status,
        expected_failure,
    ):
        self.assert_clean()

        try:
            self.client.command(insert_sql)
            results, failed = self.execute()

            self.assertEqual(
                results[check_name].status,
                expected_status,
            )
            self.assertEqual(
                results[check_name].violation_count,
                1,
            )
            self.assertEqual(failed, expected_failure)

        finally:
            self.client.command(cleanup_sql)

        self.assert_clean()

    def test_clean_baseline(self):
        self.assert_clean()

    def test_duplicate_key(self):
        self.run_scenario(
            """
            INSERT INTO data_quality_test.test_clients VALUES
            ('ORG001', 'C001', 'AUTO_DUPLICATE', '2026-01-01')
            """,
            """
            ALTER TABLE data_quality_test.test_clients
            DELETE WHERE client_id = 'C001'
            AND client_name = 'AUTO_DUPLICATE'
            AND organisation_id = 'ORG001'
            AND processing_date = '2026-01-01'
            SETTINGS mutations_sync = 1
            """,
            "client_key_unique",
            "ERROR",
            True,
        )

    def test_missing_required_field(self):
        self.run_scenario(
            """
            INSERT INTO data_quality_test.test_clients VALUES
            ('ORG001', 'AUTO_NULL', NULL, '2026-01-01')
            """,
            """
            ALTER TABLE data_quality_test.test_clients
            DELETE WHERE client_id = 'AUTO_NULL'
            SETTINGS mutations_sync = 1
            """,
            "client_name_required",
            "ERROR",
            True,
        )

    def test_cross_tenant_leak(self):
        self.run_scenario(
            """
            INSERT INTO data_quality_test.test_accounts VALUES
            ('ORG002', 'AUTO_LEAK', 'C001', 3000, '2026-01-01')
            """,
            """
            ALTER TABLE data_quality_test.test_accounts
            DELETE WHERE account_id = 'AUTO_LEAK'
            SETTINGS mutations_sync = 1
            """,
            "account_client_tenant_integrity",
            "ERROR",
            True,
        )

    def test_invalid_range(self):
        self.run_scenario(
            """
            INSERT INTO data_quality_test.test_accounts VALUES
            ('ORG001', 'AUTO_RANGE', 'C001', 15000, '2026-01-01')
            """,
            """
            ALTER TABLE data_quality_test.test_accounts
            DELETE WHERE account_id = 'AUTO_RANGE'
            SETTINGS mutations_sync = 1
            """,
            "account_balance_range",
            "ERROR",
            True,
        )

    def test_warning_only(self):
        self.run_scenario(
            """
            INSERT INTO data_quality_test.test_clients VALUES
            ('ORG001', 'AUTO_WARNING', 'Warning Client', '2026-01-01')
            """,
            """
            ALTER TABLE data_quality_test.test_clients
            DELETE WHERE client_id = 'AUTO_WARNING'
            SETTINGS mutations_sync = 1
            """,
            "client_row_count",
            "WARNING",
            False,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
