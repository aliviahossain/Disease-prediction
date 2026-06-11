import os
import sys

# Must happen before any test module imports 'backend', because
# test_integration.py calls create_app() at module level.
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-not-for-production")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "")

# Add the repo root to sys.path so 'from backend import ...' resolves
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))