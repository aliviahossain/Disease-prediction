import os

from dotenv import load_dotenv

from backend import create_app

# Load environment variables from .env file
load_dotenv()

# Create Flask app using the factory function
app = create_app()

# For Gunicorn or other WSGI servers
# Gunicorn will use "app" automatically.

if __name__ == "__main__":
    # Run locally for development
    print("\n" + "=" * 50)
    print("Starting Flask Development Server")
    print("=" * 50 + "\n")

    # Parse debug mode from environment, defaulting to False for safety
    flask_debug_env = os.environ.get("FLASK_DEBUG", "0").lower()
    flask_env = os.environ.get("FLASK_ENV", "production").lower()
    debug = flask_debug_env in ("1", "true", "yes")

    # In production, always disable debug mode
    if flask_env == "production":
        debug = False
        if flask_debug_env in ("1", "true", "yes"):
            print("[WARN] FLASK_DEBUG=1 found but FLASK_ENV=production: debug mode forcibly disabled")

    if debug:
        print("[WARN] WARNING: Debug mode is ENABLED - remote code execution possible via Werkzeug PIN!")
        print("       Ensure this is development-only!\n")
    else:
        print("[OK] Debug mode is DISABLED (secure)\n")

    app.run(debug=debug, host="0.0.0.0", port=5001, use_reloader=False)
