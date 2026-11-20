import unittest
from backend.utils.history_manager import (
    load_history,
    save_history,
    clear_history,
    get_total_predictions,
    get_risk_distribution,
)


class TestHistoryManager(unittest.TestCase):
    # The root conftest.py points DATABASE_DIR at a temporary folder, so these
    # tests run against a throwaway database and never touch real history.

    def setUp(self):
        clear_history()

    def tearDown(self):
        clear_history()

    def test_save_and_load_history(self):
        entry = {
            "Disease": "Flu",
            "Probability": 75.0,
            "Risk": "High",
            "Timestamp": "2026-07-22 12:00:00",
        }
        save_history(entry)
        history = load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["Disease"], "Flu")
        self.assertEqual(get_total_predictions(), 1)

    def test_clear_history(self):
        entry = {
            "Disease": "COVID-19",
            "Probability": 85.0,
            "Risk": "High",
            "Timestamp": "2026-07-22 12:05:00",
        }
        save_history(entry)
        self.assertEqual(get_total_predictions(), 1)

        clear_history()

        self.assertEqual(load_history(), [])
        self.assertEqual(get_total_predictions(), 0)
        self.assertEqual(get_risk_distribution(), {"Low": 0, "Moderate": 0, "High": 0})


if __name__ == "__main__":
    unittest.main()
