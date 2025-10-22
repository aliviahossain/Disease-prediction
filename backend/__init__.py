from flask import Flask
import os

def create_app():
    # Set the static and template folder paths relative to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__,
                static_folder=os.path.join(backend_dir, 'static'),
                template_folder=os.path.join(backend_dir, 'templates'))

    # Register Blueprints
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)

    from backend.routes.scalability_routes import scalability_bp
    app.register_blueprint(scalability_bp)

    return app
