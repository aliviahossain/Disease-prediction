from flask import Flask, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(backend_root, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key_here' # Change this in production!

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    
    # Register Disease Routes Blueprint
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)
    print("✅ 'disease_routes' blueprint registered successfully")
    
    # Register ML Routes Blueprint
    from backend.routes.ml_routes import ml_bp
    app.register_blueprint(ml_bp)
    print("✅ 'ml_routes' blueprint registered successfully")

    # Register Auth Routes Blueprint
    from backend.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    print("✅ 'auth_routes' blueprint registered successfully")
    
    # Register other blueprints if you have them
    try:
        from backend.routes.general_routes import general_bp
        app.register_blueprint(general_bp)
        print("✅ 'general_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'general_routes'. Error: {e}")
    
    try:
        from backend.routes.scalability_routes import scalability_bp
        app.register_blueprint(scalability_bp)
        print("✅ 'scalability_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'scalability_routes'. Error: {e}")
    
    # Create Database Tables
    with app.app_context():
        db.create_all()
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    return app