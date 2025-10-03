from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)

    from backend.routes.scalability_routes import scalability_bp
    app.register_blueprint(scalability_bp)

    return app
