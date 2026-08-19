# run.py
from backend import create_app
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

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
    print("\n" + "=" * 50)
    print("  Disease Prediction — Flask Development Server")
    print("=" * 50 + "\n")
    # SECURITY: debug mode must never be hardcoded to True. create_app()
    # already derives app.debug from FLASK_DEBUG/FLASK_ENV and forces it
    # off in production; reuse that value instead of overriding it here,
    # otherwise the Werkzeug debugger (arbitrary code execution) is always
    # reachable regardless of environment configuration.
    app.run(debug=app.debug, host="0.0.0.0", port=5001, use_reloader=False)
