import unittest

from platform_health.graph import LineageGraph


class TestLineageGraph(unittest.TestCase):

    def setUp(self):
        self.graph = LineageGraph()
        self.graph.add_dependency(
            "bronze_clients", "silver_clients"
        )
        self.graph.add_dependency(
            "silver_clients", "gold_clients"
        )

    def test_upstream(self):
        self.assertEqual(
            self.graph.upstream("silver_clients"),
            ["bronze_clients"]
        )

    def test_downstream(self):
        self.assertEqual(
            self.graph.downstream("silver_clients"),
            ["gold_clients"]
        )

    def test_ancestors(self):
        self.assertEqual(
            self.graph.ancestors("gold_clients"),
            ["bronze_clients", "silver_clients"]
        )

    def test_descendants(self):
        self.assertEqual(
            self.graph.descendants("bronze_clients"),
            ["gold_clients", "silver_clients"]
        )

    def test_no_cycles(self):
        self.assertEqual(self.graph.detect_cycles(), [])

    def test_cycle_detection(self):
        self.graph.add_dependency(
            "gold_clients", "bronze_clients"
        )
        self.assertTrue(self.graph.detect_cycles())

    def test_self_dependency(self):
        self.graph.add_dependency("table_a", "table_a")
        self.assertTrue(self.graph.detect_cycles())

    def test_orphan_detection(self):
        self.graph.add_table("isolated_table")
        self.assertEqual(
            self.graph.orphan_tables(),
            ["isolated_table"]
        )

    def test_missing_table(self):
        self.assertEqual(
            self.graph.missing_tables(
                ["bronze_clients", "silver_clients"]
            ),
            ["gold_clients"]
        )

    def test_duplicate_edge(self):
        self.graph.add_dependency(
            "bronze_clients", "silver_clients"
        )
        self.assertEqual(len(self.graph.edges), 2)


if __name__ == "__main__":
    unittest.main()
