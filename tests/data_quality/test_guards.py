import unittest

from data_quality.guards import generate_tenant_guards


class TestTenantGuards(unittest.TestCase):

    def make_guards(self, **overrides):
        options = {
            "database": "wealth_management",
            "table": "silver_clients",
            "tenant_column": "organisation_id",
            "primary_key": ["organisation_id", "client_id"],
        }
        options.update(overrides)
        return generate_tenant_guards(**options)

    def test_default_guards(self):
        checks = self.make_guards()
        self.assertEqual(len(checks), 2)
        self.assertEqual(
            {check.check_type for check in checks},
            {"null_check", "unique_key"},
        )

    def test_tenant_key_is_required(self):
        with self.assertRaises(ValueError):
            self.make_guards(primary_key=["client_id"])

    def test_row_count_guard(self):
        checks = self.make_guards(expected_count=210)
        row_check = checks[-1]

        self.assertEqual(
            row_check.check_type,
            "row_count_reconciliation",
        )
        self.assertEqual(row_check.severity, "WARNING")
        self.assertEqual(row_check.parameters["expected_count"], 210)

    def test_cross_tenant_guard(self):
        checks = self.make_guards(
            entity_column="client_id",
            reference_table="client_tenant_ownership",
        )
        self.assertEqual(checks[-1].check_type, "cross_tenant_check")

    def test_incomplete_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.make_guards(entity_column="client_id")

    def test_invalid_expected_count(self):
        with self.assertRaises(ValueError):
            self.make_guards(expected_count=-1)


if __name__ == "__main__":
    unittest.main()
