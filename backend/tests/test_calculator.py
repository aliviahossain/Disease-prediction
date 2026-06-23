import csv
import io
import importlib.util
import os
import sys
import tempfile
import unittest
import pytest

TEST_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))


def _load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_src_calculator = _load_module_from_path(
    "backend_src_calculator",
    os.path.join(BACKEND_DIR, "src", "calculator.py"),
)
_ml_model_module = _load_module_from_path(
    "backend_models_ml_model",
    os.path.join(BACKEND_DIR, "models", "ml_model.py"),
)
_utils_calculator = _load_module_from_path(
    "backend_utils_calculator",
    os.path.join(BACKEND_DIR, "utils", "calculator.py"),
)

bayesian_survival = _src_calculator.bayesian_survival
load_data = _src_calculator.load_data
display_results = _src_calculator.display_results
DiseaseMLModel = _ml_model_module.DiseaseMLModel
BayesCalculator = _utils_calculator.BayesCalculator


class TestBayesianCalculator(unittest.TestCase):
    def test_mid_range_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 0.5), 0.5, places=4)
        self.assertAlmostEqual(bayesian_survival(0.3, 0.7, 0.6), 0.4286, places=4)

    def test_low_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.01, 0.01, 0.01), 0.0001, places=4)
        self.assertAlmostEqual(bayesian_survival(0.05, 0.05, 0.05), 0.0028, places=4)

    def test_high_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.99, 0.99, 0.99), 0.9999, places=4)
        self.assertAlmostEqual(bayesian_survival(0.95, 0.95, 0.95), 0.9972, places=4)

    def test_boundary_conditions(self):
        # Prior at bounds
        self.assertAlmostEqual(bayesian_survival(0, 0.5, 0.5), 0.0, places=4)
        self.assertAlmostEqual(bayesian_survival(1, 0.5, 0.5), 1.0, places=4)
        # Sensitivity at bounds
        self.assertAlmostEqual(bayesian_survival(0.5, 0, 0.5), 0.0, places=4)
        self.assertAlmostEqual(bayesian_survival(0.5, 1, 0.5), 0.6667, places=4)
        # Specificity at bounds
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 0), 0.3333, places=4)
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 1), 1.0, places=4)

    # -----------------------------
    # Test load_data
    # -----------------------------
    def test_load_data_empty_file(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="")
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(results, [])

    def test_load_data_malformed_warn(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="")
        temp_file.write("prior,sensitivity,specificity\n0.5,abc,0.5\n")
        temp_file.close()

        captured = io.StringIO()
        sys.stdout = captured
        results = load_data(temp_file.name, strict=False)
        sys.stdout = sys.__stdout__
        os.unlink(temp_file.name)

        # Should drop row and warn
        self.assertEqual(results, [])
        self.assertIn("Warning: Dropped 1 invalid row(s)", captured.getvalue())

    def test_load_data_large_file(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="")
        writer = csv.DictWriter(
            temp_file, fieldnames=["prior", "sensitivity", "specificity"]
        )
        writer.writeheader()
        for i in range(100):
            writer.writerow(
                {"prior": 0.1 * (i % 10), "sensitivity": 0.5, "specificity": 0.5}
            )
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(len(results), 100)

    def test_load_data_coercion(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="")
        writer = csv.DictWriter(
            temp_file, fieldnames=["prior", "sensitivity", "specificity"]
        )
        writer.writeheader()
        # Out-of-range values
        writer.writerow({"prior": -0.5, "sensitivity": 1.2, "specificity": 0.5})
        # Non-numeric row
        writer.writerow({"prior": "abc", "sensitivity": 0.5, "specificity": 0.5})
        temp_file.close()

        captured = io.StringIO()
        sys.stdout = captured
        results = load_data(temp_file.name, strict=False)
        sys.stdout = sys.__stdout__
        os.unlink(temp_file.name)

        # Out-of-range values coerced to [0,1]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["prior"], 0.0)
        self.assertEqual(results[0]["sensitivity"], 1.0)
        self.assertEqual(results[0]["specificity"], 0.5)
        self.assertIn("Warning: Dropped 1 invalid row(s)", captured.getvalue())

    def test_display_results_empty(self):
        captured = io.StringIO()
        sys.stdout = captured
        display_results([])
        sys.stdout = sys.__stdout__
        self.assertEqual(captured.getvalue(), "")

    def test_display_results_output(self):
        results = [
            {"prior": 0.5, "sensitivity": 0.5, "specificity": 0.5, "posterior": 0.5},
            {
                "prior": 0.2,
                "sensitivity": 0.8,
                "specificity": 0.9,
                "posterior": bayesian_survival(0.2, 0.8, 0.9),
            },
        ]
        captured = io.StringIO()
        sys.stdout = captured
        display_results(results)
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("Prior: 0.5", output)
        self.assertIn("Specificity: 0.9", output)

    def test_verify_order_invariance_on_symptom_sequences(self):
        model = DiseaseMLModel()
        calculator = BayesCalculator()
        symptoms = ["fever", "cough", "fatigue"]

        diagnostics = calculator.verify_order_invariance(
            model=model,
            disease="influenza",
            symptoms=symptoms,
            tolerance=1e-8,
            max_permutations=6,
        )

        self.assertTrue(diagnostics["order_invariant"])
        self.assertEqual(diagnostics["tested_orderings"], 6)
        self.assertAlmostEqual(diagnostics["posterior_drift"], 0.0, places=8)
        self.assertEqual(len(diagnostics["posterior_values"]), 6)


if __name__ == "__main__":
    unittest.main()

def test_invalid_prior_raises():
    with pytest.raises(ValueError):
        bayesian_survival(-0.1, 0.5, 0.5)

def test_invalid_sensitivity_raises():
    with pytest.raises(ValueError):
        bayesian_survival(0.5, 1.2, 0.5)

def test_invalid_specificity_raises():
    with pytest.raises(ValueError):
        bayesian_survival(0.5, 0.5, -0.3)

def test_error_message_contains_parameter_name():
    with pytest.raises(ValueError) as context:
        bayesian_survival(1.5, 0.5, 0.5)

    self.assertIn("prior", str(context.exception))