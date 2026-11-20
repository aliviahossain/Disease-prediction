import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from backend.middleware.error_handler import ErrorHandler

load_dotenv()
# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
from flask_caching import Cache

cache = Cache()
csrf = CSRFProtect()


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    from backend.models.user import User

    return User.query.get(int(user_id))


def _ensure_user_profile_columns(engine):
    """Add profile columns to existing SQLite databases created before this model update."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("user")}
    profile_columns = {
        "phone": "VARCHAR(20)",
        "address": "VARCHAR(160)",
        "emergency_name": "VARCHAR(80)",
        "emergency_relation": "VARCHAR(50)",
        "emergency_phone": "VARCHAR(20)",
        "dob": "DATE",
        "gender": "VARCHAR(20)",
        "height": "FLOAT",
        "weight": "FLOAT",
        "bmi": "FLOAT",
        "allergies": "VARCHAR(200)",
        "medical_notes": "TEXT",
    }

    with engine.begin() as connection:
        for column_name, column_type in profile_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                )


# (module, blueprint attribute, required). Required blueprints fail loudly;
# optional ones only log a warning if their dependencies are missing.
_BLUEPRINTS = [
    ("backend.routes.disease_routes", "disease_bp", True),
    ("backend.routes.ml_routes", "ml_bp", False),
    ("backend.routes.auth_routes", "auth_bp", True),
    ("backend.routes.doctor_routes", "doctor_bp", False),
    ("backend.routes.history_routes", "history_bp", False),
    ("backend.routes.predict_disease_type_routes", "predict_disease_type_bp", False),
    ("backend.routes.general_routes", "general_bp", False),
    ("backend.routes.scalability_routes", "scalability_bp", False),
    ("backend.routes.chat_routes", "chat_bp", False),
    ("backend.routes.bias_routes", "bias_bp", False),
    ("backend.routes.synthetic_routes", "synthetic_bp", False),
]


def _register_blueprints(app):
    import importlib

    for module_name, attr, required in _BLUEPRINTS:
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            if required:
                raise
            print(f"[WARN] Could not import '{module_name}': {e}")
            continue
        app.register_blueprint(getattr(module, attr))
    print(f"[OK] Registered {len(app.blueprints)} blueprints")


def create_app():
    # Get the backend directory (where this __init__.py file is)
    backend_root = os.path.dirname(os.path.abspath(__file__))

    # Initialize Flask app with correct paths
    app = Flask(
        __name__,
        static_folder=os.path.join(backend_root, "static"),
        template_folder=os.path.join(backend_root, "templates"),
    )

    # SECURITY: Explicitly disable debug mode in production
    # Parse debug flag from environment, defaulting to False for safety
    flask_debug_env = os.getenv("FLASK_DEBUG", "0").lower()
    debug_mode = flask_debug_env in ("1", "true", "yes")
    flask_env = os.getenv("FLASK_ENV", "production").lower()

    # In production, always disable debug mode regardless of environment variable
    if flask_env == "production":
        debug_mode = False
        if flask_debug_env in ("1", "true", "yes"):
            print("[WARN] WARNING: FLASK_DEBUG=1 found but FLASK_ENV=production")
            print(
                "       Debug mode forcibly disabled for security. Set FLASK_ENV=development to enable debug."
            )

    app.debug = debug_mode
    if debug_mode:
        print(
            "[WARN] WARNING: Flask debug mode is ENABLED. This should NEVER be enabled in production."
        )
        print(
            "       Remote code execution is possible via the Werkzeug debugger PIN bypass."
        )
    else:
        print("[OK] Flask debug mode is DISABLED (secure)")

    # Configure Database: one dedicated store for users, passwords, profiles
    # and history (see backend/storage.py). DATABASE_URL overrides it.
    from backend.storage import get_database_uri, load_or_create_dev_secret_key

    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    print(f"[OK] Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1]}")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # SECURITY FIX: Load SECRET_KEY from environment variable
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        is_development = (
            os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1"
        )

        if is_development:
            secret_key = load_or_create_dev_secret_key()
            print("\n[WARN] WARNING: SECRET_KEY not set in environment.")
            print(
                "   Using a locally generated development key (database/.secret_key)."
            )
            print("   For production, set SECRET_KEY in your .env file!\n")
        else:
            raise ValueError(
                "\n[FAIL] CRITICAL ERROR: SECRET_KEY environment variable is required!\n"
                "   Please set SECRET_KEY in your .env file.\n"
                '   Generate one with: python -c "import secrets; print(secrets.token_hex(32))"\n'
            )

    app.config["SECRET_KEY"] = secret_key

    # SECURITY FIX: Limit upload size to 10MB to prevent disk exhaustion DoS
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    # --- Session & Cookie Security (Issue 5) --------------------------------
    # Sessions expire after 2 hours of inactivity.
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
    # Use app-specific cookie names. Browsers share cookies across all ports
    # of a host, so the default "session" name collides with any other Flask
    # app on localhost (or stale cookies from older runs). The browser then
    # sends the wrong cookie, the CSRF token never matches, and every POST
    # fails with "session expired".
    app.config["SESSION_COOKIE_NAME"] = "disease_prediction_session"
    app.config["REMEMBER_COOKIE_NAME"] = "disease_prediction_remember"
    # Prevent JavaScript from reading the session cookie (XSS mitigation).
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    # Block the cookie from being sent on cross-site navigations (CSRF mitigation).
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Only send the cookie over HTTPS in non-development environments.
    _is_dev = os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1"
    app.config["SESSION_COOKIE_SECURE"] = not _is_dev
    # Apply the same hardening to Flask-Login's "remember me" cookie.
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    # Logged-in users stay logged in for 30 days (also across server restarts).
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)
    app.config["REMEMBER_COOKIE_SECURE"] = not _is_dev
    # -------------------------------------------------------------------------

    # Validate startup configuration (environment variables and model files)
    from backend.utils.config_validator import validate_startup_config

    validate_startup_config(app)

    app.config["CACHE_TYPE"] = os.environ.get("CACHE_TYPE", "SimpleCache")
    if app.config["CACHE_TYPE"] == "RedisCache":
        app.config["CACHE_REDIS_URL"] = os.environ.get(
            "REDIS_URL", "redis://localhost:6379/0"
        )
    app.config["CACHE_DEFAULT_TIMEOUT"] = 86400

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)

    # Disable CSRF in test mode so existing tests don't break
    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False

    # --- Models -------------------------------------------------------
    # Import the models so SQLAlchemy registers them with `db` before create_all() is called below.
    # Without this import the patient_history table is never created, which is one half of the bug where history is "not being recorded".
    from backend.models.user import User  # noqa: F401
    from backend.models.prediction import PredictionHistory  # noqa: F401

    _register_blueprints(app)

    # Keep centralized error handler (from register-error-handler branch)
    ErrorHandler(app)

    # Mark every session as permanent so Flask applies PERMANENT_SESSION_LIFETIME.
    # Without this, sessions use the browser-session lifetime (close = expire).
    @app.before_request
    def _make_session_permanent():
        from flask import session as _session

        _session.permanent = True

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    with app.app_context():
        db.create_all()
        _ensure_user_profile_columns(db.engine)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app
