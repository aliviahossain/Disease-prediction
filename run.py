# run.py
"""
Application entry point.

Local development:   python run.py            -> http://127.0.0.1:5001
Production (WSGI):   gunicorn run:app
"""

import logging
import os

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# When launched directly with `python run.py` (i.e. on a developer's machine),
# default to development mode so the app starts with zero configuration:
# a throwaway SECRET_KEY is generated and GEMINI_API_KEY becomes optional.
# Values from .env or the shell always win. Production servers import
# `run:app` through gunicorn, so this branch never runs there and the
# secure production defaults in create_app() still apply.
if __name__ == "__main__":
    os.environ.setdefault("FLASK_ENV", "development")

from backend import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Startup environment checks
# ---------------------------------------------------------------------------


def _check_environment():
    """Warn about missing optional keys and fail fast on required ones."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        logger.warning(
            "\n"
            "  ⚠️  GEMINI_API_KEY is not set.\n"
            "  AI recommendation endpoints will be disabled gracefully.\n"
            "  To enable, add GEMINI_API_KEY=your_key to your .env file.\n"
        )
        # Mark key as absent so routes can check os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_AVAILABLE"] = "false"
    else:
        os.environ["GEMINI_AVAILABLE"] = "true"
        logger.info("✅ GEMINI_API_KEY detected — AI recommendations enabled.")


_check_environment()
app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    display_host = "127.0.0.1" if host in ("0.0.0.0", "") else host

    print("\n" + "=" * 50)
    print("  Disease Prediction — Flask Development Server")
    print(f"  Open: http://{display_host}:{port}/")
    print("=" * 50 + "\n")
    # SECURITY: debug mode must never be hardcoded to True. create_app()
    # already derives app.debug from FLASK_DEBUG/FLASK_ENV and forces it
    # off in production; reuse that value instead of overriding it here,
    # otherwise the Werkzeug debugger (arbitrary code execution) is always
    # reachable regardless of environment configuration.
    app.run(debug=app.debug, host=host, port=port, use_reloader=False)
