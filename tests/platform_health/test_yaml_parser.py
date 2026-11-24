import tempfile
import unittest
from pathlib import Path

from platform_health.yaml_parser import extract_yaml_lineage


class TestYAMLParser(unittest.TestCase):

    def parse(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lineage.yaml"
            path.write_text(content)
            return extract_yaml_lineage(path)

    def test_single_dependency(self):
        edges = self.parse("""
models:
  - target: wealth_management.silver_clients
    sources:
      - wealth_management.bronze_clients
""")
        self.assertEqual(edges, [(
            "wealth_management.bronze_clients",
            "wealth_management.silver_clients",
        )])

    def test_multiple_dependencies(self):
        edges = self.parse("""
models:
  - target: wealth_management.gold_activity
    sources:
      - wealth_management.silver_accounts
      - wealth_management.silver_trades
""")
        self.assertEqual(len(edges), 2)

    def test_duplicate_dependencies(self):
        edges = self.parse("""
models:
  - target: db.silver_clients
    sources:
      - db.bronze_clients
      - db.bronze_clients
""")
        self.assertEqual(len(edges), 1)

    def test_invalid_identifier(self):
        with self.assertRaises(ValueError):
            self.parse("""
models:
  - target: invalid-table
    sources:
      - db.source
""")

    def test_empty_sources(self):
        with self.assertRaises(ValueError):
            self.parse("""
models:
  - target: db.target
    sources: []
""")

    def test_empty_models(self):
        with self.assertRaises(ValueError):
            self.parse("models: []")


if __name__ == "__main__":
    unittest.main()
