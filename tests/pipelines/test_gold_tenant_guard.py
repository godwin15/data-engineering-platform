import unittest

from scripts.pipeline_config import load_models
from scripts.gold_tenant_guard import validate_gold_sql


class GoldTenantGuardTests(unittest.TestCase):

    def test_all_configured_gold_models(self):
        for name, model in load_models("gold.yaml").items():
            with self.subTest(model=name):
                self.assertTrue(
                    validate_gold_sql(model["sql"])
                )

    def test_valid_aggregation(self):
        sql = """
            SELECT organisation_id, count()
            FROM silver_accounts
            GROUP BY organisation_id
        """
        self.assertTrue(validate_gold_sql(sql))

    def test_missing_tenant_grouping(self):
        sql = """
            SELECT account_id, count()
            FROM silver_accounts
            GROUP BY account_id
        """
        with self.assertRaises(ValueError):
            validate_gold_sql(sql)

    def test_aggregation_without_grouping(self):
        with self.assertRaises(ValueError):
            validate_gold_sql(
                "SELECT count() FROM silver_accounts"
            )

    def test_valid_tenant_join(self):
        sql = """
            SELECT a.account_id
            FROM silver_accounts a
            JOIN silver_clients c
                ON a.client_id = c.client_id
                AND a.organisation_id = c.organisation_id
        """
        self.assertTrue(validate_gold_sql(sql))

    def test_cross_tenant_join(self):
        sql = """
            SELECT a.account_id
            FROM silver_accounts a
            JOIN silver_clients c
                ON a.client_id = c.client_id
        """
        with self.assertRaises(ValueError):
            validate_gold_sql(sql)

    def test_tenant_join_with_or(self):
        sql = """
            SELECT a.account_id
            FROM silver_accounts a
            JOIN silver_clients c
                ON a.client_id = c.client_id
                OR a.organisation_id = c.organisation_id
        """
        with self.assertRaises(ValueError):
            validate_gold_sql(sql)

    def test_unsafe_nested_aggregation(self):
        sql = """
            SELECT *
            FROM (
                SELECT account_id, count()
                FROM silver_accounts
                GROUP BY account_id
            ) AS totals
        """
        with self.assertRaises(ValueError):
            validate_gold_sql(sql)

    def test_non_select_statement(self):
        with self.assertRaises(ValueError):
            validate_gold_sql("DROP TABLE silver_accounts")

    def test_multiple_statements(self):
        with self.assertRaises(ValueError):
            validate_gold_sql("SELECT 1; SELECT 2")


if __name__ == "__main__":
    unittest.main()
