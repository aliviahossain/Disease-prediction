from flask import Flask, render_template
import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from backend.middleware.error_handler import ErrorHandler
from sqlalchemy import inspect, text
from dotenv import load_dotenv
load_dotenv()
# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from backend.models.user import User
    return User.query.get(int(user_id))


from datetime import datetime


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


def create_app():
    # Get the backend directory (where this __init__.py file is)
    backend_root = os.path.dirname(os.path.abspath(__file__))

    print(f"Backend root: {backend_root}")
    print(f"Templates folder: {os.path.join(backend_root, 'templates')}")

    # Initialize Flask app with correct paths
    app = Flask(__name__,
                static_folder=os.path.join(backend_root, 'static'),
                template_folder=os.path.join(backend_root, 'templates')
            )

    # Configure Database
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Compatibility fix for newer SQLAlchemy versions and Heroku-style URLs
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
            backend_root, "site.db"
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ SECURITY FIX: Load SECRET_KEY from environment variable
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        is_development = (
            os.getenv("FLASK_ENV") == "development"
            or os.getenv("FLASK_DEBUG") == "1"
        )

        if is_development:
            secret_key = secrets.token_hex(32)
            print("\n⚠️  WARNING: SECRET_KEY not set in environment.")
            print("   Using random key for development only.")
            print("   For production, set SECRET_KEY in your .env file!\n")
        else:
            raise ValueError(
                "\n❌ CRITICAL ERROR: SECRET_KEY environment variable is required!\n"
                "   Please set SECRET_KEY in your .env file.\n"
                "   Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            )

    app.config["SECRET_KEY"] = secret_key

    # Validate startup configuration (environment variables and model files)
    from backend.utils.config_validator import validate_startup_config
    validate_startup_config(app)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # --- Models -------------------------------------------------------
    # Import the models so SQLAlchemy registers them with `db` before create_all() is called below.
    # Without this import the patient_history table is never created, which is one half of the bug where history is "not being recorded".
    from backend.models import user
    from backend.models import patient_history
    
    # Register Disease Routes Blueprint
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)
    print("'disease_routes' blueprint registered successfully")

    # Register ML Routes Blueprint
    try:
        from backend.routes.ml_routes import ml_bp  # type: ignore
        app.register_blueprint(ml_bp)
        print("'ml_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import 'ml_routes'. Error: {e}")

    # Register Auth Routes Blueprint
    from backend.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    print("'auth_routes' blueprint registered successfully")

    # Register Doctor Dashboard Routes Blueprint
    try:
        from backend.routes.doctor_routes import doctor_bp
        app.register_blueprint(doctor_bp)
        print("'doctor_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import 'doctor_routes'. Error: {e}")

    try:
        from backend.routes.history_routes import history_bp
        app.register_blueprint(history_bp)
        print("✅ 'history_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'history_routes'. Error: {e}")

    try:
        from backend.routes.predict_disease_type_routes import predict_disease_type_bp
        app.register_blueprint(predict_disease_type_bp)
        print("'predict_disease_type_bp_routes' blueprint registered successfully")
    except ImportError as e:
        print(
            f"Warning: Could not import 'predict_disease_type_bp_routes'. Error: {e}"
        )

    try:
        from backend.routes.general_routes import general_bp
        app.register_blueprint(general_bp)
        print("'general_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import 'general_routes'. Error: {e}")

    try:
        from backend.routes.scalability_routes import scalability_bp
        app.register_blueprint(scalability_bp)
        print("'scalability_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'scalability_routes'. Error: {e}")

    try:
        from backend.routes.chat_routes import chat_bp
        app.register_blueprint(chat_bp)
        print("✅ 'chat_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'chat_routes'. Error: {e}")

    # ✅ Keep bias routes (from main branch)
    try:
        from backend.routes.bias_routes import bias_bp
        app.register_blueprint(bias_bp)
        print("✅ 'bias_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'bias_routes'. Error: {e}")

    # ✅ Keep centralized error handler (from register-error-handler branch)
    ErrorHandler(app)

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
