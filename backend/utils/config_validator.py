"""
Configuration and model file validator for fail-fast startup checks.
"""

import os


def validate_startup_config(app):
    """
    Validates that necessary environment variables and model files are present.
    In production mode, raises a ValueError/FileNotFoundError if any are missing or invalid.  # noqa: E501
    In development mode, prints/logs high-visibility warning messages to standard output.  # noqa: E501
    """
    # 1. Determine environment mode
    flask_env = os.getenv("FLASK_ENV")
    flask_debug = os.getenv("FLASK_DEBUG")
    is_production = (
        flask_env == "production"
        and flask_debug != "1"
        and flask_env != "development"
    )

    # 2. Check SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if is_production:
        if not secret_key:
            raise ValueError(
                "\n[ERROR] CRITICAL ERROR: SECRET_KEY environment variable is required in production!\n"  # noqa: E501
                "   Please set SECRET_KEY in your .env file or environment settings.\n"  # noqa: E501
            )
        if len(secret_key) < 16:
            raise ValueError(
                f"\n[ERROR] CRITICAL ERROR: SECRET_KEY is too weak! Got length {len(secret_key)}, expected at least 16 characters.\n"  # noqa: E501
                "   Please generate a strong random key for production.\n"
            )

    # 3. Check GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        if is_production:
            raise ValueError(
                "\n[ERROR] CRITICAL ERROR: GEMINI_API_KEY environment variable is required in production!\n"  # noqa: E501
                "   Please set GEMINI_API_KEY in your environment/Render configuration.\n"  # noqa: E501
            )
        else:
            print("\n=======================================================")
            print("[WARN] WARNING: GEMINI_API_KEY is not set in development!")
            print("   AI-powered recommendations & chatbot widgets will")
            print("   fail at runtime with a Configuration Error.")
            print("=======================================================\n")

    # 4. Check Machine Learning Model Files
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_to_check = {
        "eyes": {
            "name": "eye_disease_resnet50_fp16.keras",
            "path": os.path.join(
                backend_dir,
                "models",
                "resnet50_models",
                "eye_disease_resnet50_fp16.keras",
            ),
        },
        "skin": {
            "name": "skin_model.tflite",
            "path": os.path.join(
                backend_dir, "models", "resnet50_models", "skin_model.tflite"
            ),
        },
    }

    for model_type, info in models_to_check.items():
        model_path = info["path"]
        if not os.path.exists(model_path):
            if is_production:
                raise FileNotFoundError(
                    f"\n[ERROR] CRITICAL ERROR: Required ML model file '{info['name']}' not found at:\n"  # noqa: E501
                    f"   {model_path}\n"
                    f"   Please ensure all models are committed or pulled before starting in production.\n"  # noqa: E501
                )
            else:
                print(
                    "\n======================================================="
                )
                print(
                    f"[WARN] WARNING: ML model file '{info['name']}' not found!"  # noqa: E501
                )
                print(f"   Path checked: {model_path}")
                print(
                    f"   Image-based predictions for '{model_type}' will fail at runtime."  # noqa: E501
                )
                print(
                    "=======================================================\n"
                )
