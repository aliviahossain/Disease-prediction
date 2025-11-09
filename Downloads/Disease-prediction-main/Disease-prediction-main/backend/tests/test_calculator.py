import unittest
import tempfile
import os
import csv
import io
import sys
from src.calculator import bayesian_survival, load_data, display_results

class TestBayesianCalculator(unittest.TestCase):


    def test_mid_range_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 0.5), 0.5, places=4)
        self.assertAlmostEqual(bayesian_survival(0.3, 0.7, 0.6), 0.5385, places=4)

    def test_low_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.01, 0.01, 0.01), 0.0099, places=4)
        self.assertAlmostEqual(bayesian_survival(0.05, 0.05, 0.05), 0.0526, places=4)

    def test_high_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.99, 0.99, 0.99), 0.99, places=4)
        self.assertAlmostEqual(bayesian_survival(0.95, 0.95, 0.95), 0.95, places=4)

    def test_boundary_conditions(self):
        # Prior at bounds
        self.assertAlmostEqual(bayesian_survival(0, 0.5, 0.5), 0.0, places=4)
        self.assertAlmostEqual(bayesian_survival(1, 0.5, 0.5), 1.0, places=4)
        # Sensitivity at bounds
        self.assertAlmostEqual(bayesian_survival(0.5, 0, 0.5), 0.0, places=4)
        self.assertAlmostEqual(bayesian_survival(0.5, 1, 0.5), 0.6667, places=4)
        # Specificity at bounds
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 0), 0.5, places=4)
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 1), 0.5, places=4)

    # -----------------------------
    # Test load_data
    # -----------------------------
    def test_load_data_empty_file(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(results, [])

    def test_load_data_malformed_warn(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
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
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=['prior','sensitivity','specificity'])
        writer.writeheader()
        for i in range(100):
            writer.writerow({'prior': 0.1*(i%10),'sensitivity':0.5,'specificity':0.5})
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(len(results), 100)

    def test_load_data_coercion(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=['prior','sensitivity','specificity'])
        writer.writeheader()
        # Out-of-range values
        writer.writerow({'prior': -0.5, 'sensitivity': 1.2, 'specificity': 0.5})
        # Non-numeric row
        writer.writerow({'prior': 'abc', 'sensitivity': 0.5, 'specificity': 0.5})
        temp_file.close()

        captured = io.StringIO()
        sys.stdout = captured
        results = load_data(temp_file.name, strict=False)
        sys.stdout = sys.__stdout__
        os.unlink(temp_file.name)

        # Out-of-range values coerced to [0,1]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['prior'], 0.0)
        self.assertEqual(results[0]['sensitivity'], 1.0)
        self.assertEqual(results[0]['specificity'], 0.5)
        self.assertIn("Warning: Dropped 1 invalid row(s)", captured.getvalue())


    def test_display_results_empty(self):
        captured = io.StringIO()
        sys.stdout = captured
        display_results([])
        sys.stdout = sys.__stdout__
        self.assertEqual(captured.getvalue(), "")

    def test_display_results_output(self):
        results = [
            {'prior': 0.5, 'sensitivity':0.5, 'specificity':0.5, 'posterior':0.5},
            {'prior': 0.2, 'sensitivity':0.8, 'specificity':0.9, 'posterior': bayesian_survival(0.2,0.8,0.9)}
        ]
        captured = io.StringIO()
        sys.stdout = captured
        display_results(results)
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("Prior: 0.5", output)
        self.assertIn("Specificity: 0.9", output)

if __name__ == "__main__":
    unittest.main()
