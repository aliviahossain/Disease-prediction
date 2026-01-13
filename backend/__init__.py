from flask import Flask, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

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

def create_app():
    # Get the backend directory (where this __init__.py file is)
    backend_root = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Backend root: {backend_root}")
    print(f"Templates folder: {os.path.join(backend_root, 'templates')}")
    
    # Initialize Flask app with correct paths
    app = Flask(
        __name__,
        static_folder=os.path.join(backend_root, 'static'),
        template_folder=os.path.join(backend_root, 'templates')
    )

    # Configure Database
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(backend_root, "site.db")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key_here' # Change this in production!

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
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
    
    # Register other blueprints if you have them
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
        print(f"Warning: Could not import 'predict_disease_type_bp_routes'. Error: {e}")

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
    
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    with app.app_context():
        db.create_all()

    return app