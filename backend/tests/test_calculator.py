import unittest
from src.calculator import bayesian_survival, load_data, display_results

class TestBayesianCalculator(unittest.TestCase):
    def test_load_data_empty_file(self):
        import tempfile, os
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(results, [])

    def test_load_data_malformed(self):
        import tempfile, os
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        temp_file.write(b"prior,sensitivity,specificity\n0.5,abc,0.5\n")
        temp_file.close()
        with self.assertRaises(Exception):
            load_data(temp_file.name)
        os.unlink(temp_file.name)

    def test_display_results_empty(self):
        import io, sys
        captured = io.StringIO()
        sys.stdout = captured
        display_results([])
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertEqual(output, "")

    def test_load_data_large_file(self):
        import tempfile, os, csv
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=['prior', 'sensitivity', 'specificity'])
        writer.writeheader()
        for i in range(100):
            writer.writerow({'prior': 0.1 * (i % 10), 'sensitivity': 0.5, 'specificity': 0.5})
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(len(results), 100)
    def test_load_data(self):
        # Create a temporary CSV file
        import tempfile, os, csv
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=['prior', 'sensitivity', 'specificity'])
        writer.writeheader()
        writer.writerow({'prior': 0.5, 'sensitivity': 0.5, 'specificity': 0.5})
        writer.writerow({'prior': 0.2, 'sensitivity': 0.8, 'specificity': 0.9})
        temp_file.close()
        results = load_data(temp_file.name)
        os.unlink(temp_file.name)
        self.assertEqual(len(results), 2)
        self.assertAlmostEqual(results[0]['posterior'], 0.5, places=4)
        self.assertAlmostEqual(results[1]['posterior'], bayesian_survival(0.2, 0.8, 0.9), places=4)

    def test_display_results(self):
        # Capture print output
        import io, sys
        results = [
            {'prior': 0.5, 'sensitivity': 0.5, 'specificity': 0.5, 'posterior': 0.5},
            {'prior': 0.2, 'sensitivity': 0.8, 'specificity': 0.9, 'posterior': bayesian_survival(0.2, 0.8, 0.9)}
        ]
        captured = io.StringIO()
        sys.stdout = captured
        display_results(results)
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "Prior: 0.5" in output
        assert "Specificity: 0.9" in output

    def test_mid_range_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.5, 0.5, 0.5), 0.5, places=4)
        self.assertAlmostEqual(bayesian_survival(0.3, 0.7, 0.6), 0.5385, places=4)

    def test_low_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.01, 0.01, 0.01), 0.0099, places=4)
        self.assertAlmostEqual(bayesian_survival(0.05, 0.05, 0.05), 0.0526, places=4)

    def test_high_probabilities(self):
        self.assertAlmostEqual(bayesian_survival(0.99, 0.99, 0.99), 0.99, places=4)
        self.assertAlmostEqual(bayesian_survival(0.95, 0.95, 0.95), 0.95, places=4)
    def test_typical_cases(self):
        # Common medical test scenarios
        self.assertAlmostEqual(bayesian_survival(0.01, 0.99, 0.95), 0.1664, places=4)
        self.assertAlmostEqual(bayesian_survival(0.10, 0.90, 0.90), 0.5, places=4)
        self.assertAlmostEqual(bayesian_survival(0.20, 0.85, 0.80), 0.5313, places=4)

    def test_high_specificity(self):
        # High specificity, moderate sensitivity
        self.assertAlmostEqual(bayesian_survival(0.15, 0.75, 0.99), 0.9195, places=4)

    def test_high_sensitivity(self):
        # High sensitivity, moderate specificity
        self.assertAlmostEqual(bayesian_survival(0.15, 0.99, 0.75), 0.3951, places=4)

    def test_bayesian_survival(self):
        self.assertAlmostEqual(bayesian_survival(0.95, 0.90, 0.85), 0.9811, places=4)
        self.assertAlmostEqual(bayesian_survival(0.80, 0.85, 0.90), 0.9444, places=4)
        self.assertAlmostEqual(bayesian_survival(0.60, 0.75, 0.80), 0.7500, places=4)
        # Random valid values
        self.assertAlmostEqual(bayesian_survival(0.25, 0.5, 0.75), 0.3636, places=4)
        self.assertAlmostEqual(bayesian_survival(0.33, 0.67, 0.89), 0.6872, places=4)
        # Float precision check
        self.assertAlmostEqual(bayesian_survival(0.1234, 0.5678, 0.9101), 0.4412, places=4)

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
        def test_edge_cases(self):
            # All probabilities at 0
            self.assertAlmostEqual(bayesian_survival(0, 0, 0), 0.0, places=4)
            # All probabilities at 1
            self.assertAlmostEqual(bayesian_survival(1, 1, 1), 1.0, places=4)
            # Prior at 0, sensitivity and specificity at 1
            self.assertAlmostEqual(bayesian_survival(0, 1, 1), 0.0, places=4)
            # Prior at 1, sensitivity and specificity at 0
            self.assertAlmostEqual(bayesian_survival(1, 0, 0), 0.0, places=4)

        def test_invalid_values(self):
            # Negative values
            with self.assertRaises(Exception):
                bayesian_survival(-0.1, 0.9, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, -0.1, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, 0.9, -0.1)
            # Values greater than 1
            with self.assertRaises(Exception):
                bayesian_survival(1.1, 0.9, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, 1.1, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, 0.9, 1.1)

        def test_invalid_types(self):
            # Non-float inputs
            with self.assertRaises(Exception):
                bayesian_survival("0.5", 0.9, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, "0.9", 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, 0.9, "0.9")
            with self.assertRaises(Exception):
                bayesian_survival(None, 0.9, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, None, 0.9)
            with self.assertRaises(Exception):
                bayesian_survival(0.5, 0.9, None)

if __name__ == "__main__":
    unittest.main()
