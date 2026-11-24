import tempfile
import unittest
from pathlib import Path

from data_quality.schema import load_config, discover_configs


VALID_CONFIG = """
database: wealth_management
table: silver_clients
checks:
  - name: organisation_id_required
    type: null_check
    column: organisation_id
    severity: ERROR
"""


class TestQualitySchema(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "clients.yaml"

    def write_config(self, content):
        self.path.write_text(content, encoding="utf-8")
        return self.path

    def test_valid_config(self):
        checks = load_config(self.write_config(VALID_CONFIG))
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].check_type, "null_check")
        self.assertEqual(checks[0].severity, "ERROR")

    def test_invalid_check_type(self):
        config = VALID_CONFIG.replace("null_check", "unknown_check")
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_invalid_severity(self):
        config = VALID_CONFIG.replace("ERROR", "CRITICAL")
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_missing_database(self):
        config = VALID_CONFIG.replace(
            "database: wealth_management\n", ""
        )
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_duplicate_check_names(self):
        config = VALID_CONFIG + """
  - name: organisation_id_required
    type: null_check
    column: client_id
    severity: WARNING
"""
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_invalid_sql_identifier(self):
        config = VALID_CONFIG.replace(
            "silver_clients", "silver_clients;DROP_TABLE"
        )
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_empty_checks(self):
        config = """
database: wealth_management
table: silver_clients
checks: []
"""
        with self.assertRaises(ValueError):
            load_config(self.write_config(config))

    def test_discovery(self):
        self.write_config(VALID_CONFIG)
        checks = discover_configs(self.temp_dir.name)
        self.assertEqual(len(checks), 1)


if __name__ == "__main__":
    unittest.main()
