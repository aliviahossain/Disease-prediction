import os
import sys
import tempfile

# Must happen before any test module imports 'backend', because
# test_integration.py calls create_app() at module level.
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-not-for-production")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "")

# Isolate ALL persistent storage for the test run. Without this, tests would
# read/write the real database in database/ (users, history) and could wipe
# real accounts or prediction history.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="disease_prediction_tests_")
os.environ["DATABASE_DIR"] = _TEST_DATA_DIR
os.environ["HISTORY_DATA_DIR"] = _TEST_DATA_DIR

# Add the repo root to sys.path so 'from backend import ...' resolves
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
