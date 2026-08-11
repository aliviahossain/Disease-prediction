import os
import json
import unittest
from backend.utils.history_manager import (
    load_history,
    save_history,
    clear_history,
    get_total_predictions,
    get_risk_distribution,
    HISTORY_FILE,
)


class TestHistoryManager(unittest.TestCase):

    def setUp(self):
        """Ensure clean history file state before each test."""
        self.backup = None
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                self.backup = f.read()

        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

    def tearDown(self):
        """Restore previous history file state after each test."""
        if self.backup is not None:
            with open(HISTORY_FILE, "w") as f:
                f.write(self.backup)
        elif os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

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
