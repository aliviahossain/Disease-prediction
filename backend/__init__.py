from flask import Flask, render_template
import os
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
    
    # Register Disease Routes Blueprint
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)
    print("✅ 'disease_routes' blueprint registered successfully")
    
    # Register ML Routes Blueprint
    from backend.routes.ml_routes import ml_bp
    app.register_blueprint(ml_bp)
    print("✅ 'ml_routes' blueprint registered successfully")
    
    # Register other blueprints if you have them
    try:
        from backend.routes.general_routes import general_bp
        app.register_blueprint(general_bp)
        print("✅ 'general_routes' blueprint registered successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not import 'general_routes'. Error: {e}")
    
    try:
from flask import Flask, render_template
import os
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
    
    # Register Disease Routes Blueprint
    from backend.routes.disease_routes import disease_bp
    app.register_blueprint(disease_bp)
    print("✅ 'disease_routes' blueprint registered successfully")
    
    # Register ML Routes Blueprint
    from backend.routes.ml_routes import ml_bp
    app.register_blueprint(ml_bp)
    print("✅ 'ml_routes' blueprint registered successfully")
    
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
    
    # Load translations
    import json
    try:
        with open(os.path.join(backend_root, 'translations.json'), 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading translations: {e}")
        translations = {}

    @app.context_processor
    def inject_global_vars():
        # Get language from query param or cookie (default to 'en')
        from flask import request
        lang = request.args.get('lang', request.cookies.get('lang', 'en'))
        
        # Fallback to English if language not found
        if lang not in translations:
            lang = 'en'
            
        return {
            "current_year": datetime.utcnow().year,
            "t": translations.get(lang, {}),
            "current_lang": lang,
            "available_langs": {
                "en": "English",
                "hi": "हिंदी (Hindi)",
                "ta": "தமிழ் (Tamil)",
                "te": "తెలుగు (Telugu)"
            }
        }

    return app