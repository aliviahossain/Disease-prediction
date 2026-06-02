from flask import Flask
from backend.routes.ml_routes import ml_bp

def create_app():
    app = Flask(__name__)

    # Register ML routes
    app.register_blueprint(ml_bp)

    return app