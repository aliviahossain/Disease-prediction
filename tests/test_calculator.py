import unittest
from src.calculator import bayesian_survival

class TestBayesianCalculator(unittest.TestCase):

    def test_bayesian_survival(self):
        self.assertAlmostEqual(bayesian_survival(0.95, 0.90, 0.85), 0.9811, places=4)
        self.assertAlmostEqual(bayesian_survival(0.80, 0.85, 0.90), 0.9444, places=4)
        self.assertAlmostEqual(bayesian_survival(0.60, 0.75, 0.80), 0.7500, places=4)

if __name__ == "__main__":
    unittest.main()
