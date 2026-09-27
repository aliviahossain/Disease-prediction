"""
Authentication helpers for the Streamlit analytics dashboard (dashboard.py).

The dashboard has historically been served with no authentication layer at
all: anyone who could reach the server's IP on port 8501 got full access to
aggregate patient prediction data. These helpers gate access behind a shared
password read from DASHBOARD_PASSWORD, kept separate from dashboard.py so
the logic can be unit tested without a running Streamlit session.
"""

import hmac
import os


def is_dashboard_auth_configured() -> bool:
    """Return True when a DASHBOARD_PASSWORD has been set in the environment."""
    return bool(os.getenv("DASHBOARD_PASSWORD", "").strip())


def is_production_environment() -> bool:
    """Mirror the production check used elsewhere in the app (config_validator)."""
    flask_env = os.getenv("FLASK_ENV")
    flask_debug = os.getenv("FLASK_DEBUG")
    return flask_env == "production" and flask_debug != "1"


def verify_dashboard_password(candidate: str, expected: str) -> bool:
    """
    Constant-time comparison of a submitted password against the configured
    one, so response timing cannot be used to guess the password character
    by character.
    """
    if not candidate or not expected:
        return False
    return hmac.compare_digest(candidate, expected)
