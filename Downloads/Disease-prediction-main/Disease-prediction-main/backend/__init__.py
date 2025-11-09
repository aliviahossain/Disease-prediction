from flask import Flask, render_template
import os

def create_app():
    # Get absolute backend directory path
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Initialize Flask app with static and templates folders
    app = Flask(
        __name__,
        static_folder=os.path.join(backend_dir, 'static'),
        template_folder=os.path.join(backend_dir, 'templates')
    )

    # -----------------------------
    # Register Blueprints (if needed)
    # -----------------------------
    try:
        from backend.routes.disease_routes import disease_bp
        app.register_blueprint(disease_bp)
    except ImportError:
        print("⚠️ Warning: 'disease_routes' blueprint not found. Skipping...")

    try:
        from backend.routes.scalability_routes import scalability_bp
        app.register_blueprint(scalability_bp)
    except ImportError:
        print("⚠️ Warning: 'scalability_routes' blueprint not found. Skipping...")

    # -----------------------------
    # Add General Routes (Help, Home)
    # -----------------------------
    @app.route('/')
    def home():
        """Main Homepage"""
        return render_template('main.html')

    @app.route('/help')
    def help_page():
        """Help / Glossary Page"""
        return render_template('help.html')

    # Optional: Scalability fallback (in case blueprint missing)
    @app.route('/scalability')
    def scalability_page():
        """Scalability Page"""
        return render_template('scalability.html')

    return app
