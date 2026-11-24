import unittest

from platform_health.lineage import build_lineage


class TestUnifiedLineage(unittest.TestCase):

    def setUp(self):
        self.graph, self.errors = build_lineage()

    def test_no_parser_errors(self):
        self.assertEqual(self.errors, [])

    def test_core_table_coverage(self):
        self.assertEqual(len(self.graph.nodes), 23)

    def test_dependency_count(self):
        self.assertEqual(len(self.graph.edges), 18)

    def test_no_cycles(self):
        self.assertEqual(self.graph.detect_cycles(), [])

    def test_no_orphans(self):
        self.assertEqual(self.graph.orphan_tables(), [])

    def test_gold_activity_dependencies(self):
        self.assertEqual(
            self.graph.upstream(
                "wealth_management.gold_account_activity"
            ),
            [
                "wealth_management.silver_accounts",
                "wealth_management.silver_fees",
                "wealth_management.silver_trades",
                "wealth_management.silver_transactions",
            ],
        )

    def test_bronze_impact_analysis(self):
        descendants = self.graph.descendants(
            "wealth_management.bronze_accounts"
        )

        self.assertIn(
            "wealth_management.gold_account_activity",
            descendants,
        )


if __name__ == "__main__":
    unittest.main()
