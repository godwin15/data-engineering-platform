import unittest

from platform_health.sql_parser import extract_sql_lineage


class TestSQLParser(unittest.TestCase):

    def test_simple_insert(self):
        sql = """
        INSERT INTO silver_clients
        SELECT * FROM bronze_clients
        """

        self.assertEqual(
            extract_sql_lineage(sql),
            [(
                "wealth_management.bronze_clients",
                "wealth_management.silver_clients"
            )]
        )

    def test_join_dependencies(self):
        sql = """
        INSERT INTO gold_activity
        SELECT a.account_id
        FROM silver_accounts a
        JOIN silver_trades t
        ON a.account_id = t.account_id
        """

        self.assertEqual(
            len(extract_sql_lineage(sql)), 2
        )

    def test_nested_query(self):
        sql = """
        INSERT INTO silver_accounts
        SELECT * FROM (
            SELECT * FROM bronze_accounts
        ) AS records
        """

        self.assertEqual(
            extract_sql_lineage(sql),
            [(
                "wealth_management.bronze_accounts",
                "wealth_management.silver_accounts"
            )]
        )

    def test_cte_alias_excluded(self):
        sql = """
        INSERT INTO silver_history
        WITH snapshots AS (
            SELECT * FROM bronze_clients
        )
        SELECT * FROM snapshots
        """

        self.assertEqual(
            extract_sql_lineage(sql),
            [(
                "wealth_management.bronze_clients",
                "wealth_management.silver_history"
            )]
        )

    def test_multiple_statements(self):
        sql = """
        TRUNCATE TABLE silver_clients;
        INSERT INTO silver_clients
        SELECT * FROM bronze_clients;
        """

        self.assertEqual(
            len(extract_sql_lineage(sql)), 1
        )

    def test_comments_ignored(self):
        sql = """
        -- SELECT * FROM fake_table
        INSERT INTO silver_clients
        SELECT * FROM bronze_clients
        """

        self.assertEqual(
            len(extract_sql_lineage(sql)), 1
        )

    def test_qualified_tables(self):
        sql = """
        INSERT INTO analytics.gold_clients
        SELECT * FROM staging.silver_clients
        """

        self.assertEqual(
            extract_sql_lineage(sql),
            [(
                "staging.silver_clients",
                "analytics.gold_clients"
            )]
        )


if __name__ == "__main__":
    unittest.main()
