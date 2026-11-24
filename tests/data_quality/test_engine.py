import unittest

from data_quality.adapters.fake import FakeCountAdapter
from data_quality.engine import QualityEngine
from data_quality.schema import QualityCheck


def make_check(name, severity="ERROR"):
    return QualityCheck(
        database="wealth_management",
        table="silver_clients",
        name=name,
        check_type="null_check",
        severity=severity,
        parameters={"column": "organisation_id"},
    )


class TestQualityEngine(unittest.TestCase):

    def test_clean_data_passes(self):
        engine = QualityEngine(FakeCountAdapter())
        results = engine.execute([make_check("required_org")])

        self.assertEqual(results[0].status, "PASS")
        self.assertEqual(results[0].violation_count, 0)
        self.assertFalse(engine.should_fail_pipeline(results))

    def test_error_stops_pipeline(self):
        engine = QualityEngine(
            FakeCountAdapter({"required_org": 3})
        )
        results = engine.execute([make_check("required_org")])

        self.assertEqual(results[0].status, "ERROR")
        self.assertEqual(results[0].violation_count, 3)
        self.assertTrue(engine.should_fail_pipeline(results))

    def test_warning_does_not_stop_pipeline(self):
        engine = QualityEngine(
            FakeCountAdapter({"row_count": 2})
        )
        results = engine.execute([
            make_check("row_count", severity="WARNING")
        ])

        self.assertEqual(results[0].status, "WARNING")
        self.assertFalse(engine.should_fail_pipeline(results))

    def test_multiple_checks(self):
        engine = QualityEngine(
            FakeCountAdapter({"duplicate_keys": 2})
        )
        checks = [
            make_check("required_org"),
            make_check("duplicate_keys"),
        ]
        results = engine.execute(checks)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, "PASS")
        self.assertEqual(results[1].status, "ERROR")

    def test_negative_count_rejected(self):
        engine = QualityEngine(
            FakeCountAdapter({"required_org": -1})
        )

        with self.assertRaises(ValueError):
            engine.execute([make_check("required_org")])

    def test_noninteger_count_rejected(self):
        engine = QualityEngine(
            FakeCountAdapter({"required_org": "0"})
        )

        with self.assertRaises(ValueError):
            engine.execute([make_check("required_org")])


if __name__ == "__main__":
    unittest.main()
