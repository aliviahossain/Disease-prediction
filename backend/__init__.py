from flask import Flask, render_template
import os

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
    
    # Register Disease Routes Blueprint
    try:
        from backend.routes.disease_routes import disease_bp
        app.register_blueprint(disease_bp)
        print("✅ 'disease_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'disease_routes' blueprint. Error: {e}")
    
    # Register ML Routes Blueprint
    try:
        from backend.routes.ml_routes import ml_bp
        app.register_blueprint(ml_bp)
        print("✅ 'ml_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'ml_routes' blueprint. Error: {e}")
    
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
    
    return app