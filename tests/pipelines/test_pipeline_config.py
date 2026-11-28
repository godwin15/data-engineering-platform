import unittest

from scripts.pipeline_config import (
    load_models,
    validate_identifier,
)


class PipelineConfigurationTests(unittest.TestCase):

    def test_silver_python_models(self):
        models = load_models("silver_python.yaml")
        self.assertEqual(len(models), 4)

    def test_silver_sql_models(self):
        models = load_models("silver_sql.yaml")
        self.assertEqual(len(models), 6)

    def test_gold_models(self):
        models = load_models("gold.yaml")
        self.assertEqual(len(models), 3)

    def test_silver_total_coverage(self):
        python_models = load_models("silver_python.yaml")
        sql_models = load_models("silver_sql.yaml")

        self.assertFalse(
            set(python_models) & set(sql_models)
        )

        self.assertEqual(
            len(set(python_models) | set(sql_models)),
            10
        )

    def test_silver_primary_keys(self):
        for model in load_models("silver_python.yaml").values():
            self.assertIn(model["key"], model["columns"])

    def test_gold_select_queries(self):
        for model in load_models("gold.yaml").values():
            self.assertTrue(
                model["sql"].strip().upper().startswith("SELECT")
            )

    def test_invalid_identifier(self):
        with self.assertRaises(ValueError):
            validate_identifier("invalid; DROP TABLE")

    def test_valid_identifier(self):
        self.assertEqual(
            validate_identifier("silver_clients"),
            "silver_clients"
        )


if __name__ == "__main__":
    unittest.main()
