import json
import os

# =========================
# HISTORY FILE PATH
# =========================
HISTORY_FILE = "prediction_history.json"


# =========================
# CREATE FILE IF NOT EXISTS
# =========================
def initialize_history_file():

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)


# =========================
# LOAD HISTORY
# =========================
def load_history():

    initialize_history_file()

    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)

    except json.JSONDecodeError:
        return []


# =========================
# SAVE NEW ENTRY
# =========================
def save_history(entry):

    history = load_history()

    history.append(entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


# =========================
# CLEAR HISTORY
# =========================
def clear_history():

    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)


# =========================
# GET TOTAL PREDICTIONS
# =========================
def get_total_predictions():

    history = load_history()

    return len(history)


# =========================
# GET RISK COUNTS
# =========================
def get_risk_distribution():

    history = load_history()

    risk_counts = {"Low": 0, "Moderate": 0, "High": 0}

    for entry in history:
        risk = entry.get("Risk")

        if risk in risk_counts:
            risk_counts[risk] += 1

    return risk_counts
