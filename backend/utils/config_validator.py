"""
Configuration and model file validator for fail-fast startup checks.
"""

import os


def validate_startup_config(app):
    """
    Validates that necessary environment variables and model files are present.
    In production mode, raises a ValueError/FileNotFoundError if any are missing or invalid.
    In development mode, prints/logs high-visibility warning messages to standard output.
    """
    # 1. Determine environment mode
    flask_env = os.getenv("FLASK_ENV")
    flask_debug = os.getenv("FLASK_DEBUG")
    is_production = (
        flask_env == "production" and flask_debug != "1" and flask_env != "development"
    )

    # 2. Check SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if is_production and not secret_key:
        raise ValueError(
            "\n[ERROR] CRITICAL ERROR: SECRET_KEY environment variable is required in production!\n"
            "   Please set SECRET_KEY in your .env file or environment settings.\n"
        )

    # A weak, human-guessable SECRET_KEY is just as forgeable as a hardcoded
    # default: session cookies signed with it can be forged by anyone who
    # can brute-force or guess the short value. This check previously only
    # ran when is_production was True, so a short SECRET_KEY set in a
    # development or staging environment (a common misconfiguration) was
    # silently accepted with no warning at all. Enforce it whenever a key
    # was explicitly provided, regardless of environment; the auto-generated
    # secrets.token_hex(32) fallback used when no key is set is always well
    # above this threshold, so this never blocks the zero-config dev path.
    if secret_key and len(secret_key) < 16:
        message = (
            f"SECRET_KEY is too weak! Got length {len(secret_key)}, expected at least 16 characters.\n"
            "   Please generate a strong random key: "
            'python -c "import secrets; print(secrets.token_hex(32))"\n'
        )
        if is_production:
            raise ValueError(f"\n[ERROR] CRITICAL ERROR: {message}")
        raise ValueError(f"\n[ERROR] CONFIGURATION ERROR: {message}")

    # 3. Check GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        if is_production:
            raise ValueError(
                "\n[ERROR] CRITICAL ERROR: GEMINI_API_KEY environment variable is required in production!\n"
                "   Please set GEMINI_API_KEY in your environment/Render configuration.\n"
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
                    f"\n[ERROR] CRITICAL ERROR: Required ML model file '{info['name']}' not found at:\n"
                    f"   {model_path}\n"
                    f"   Please ensure all models are committed or pulled before starting in production.\n"
                )
            else:
                print("\n=======================================================")
                print(f"[WARN] WARNING: ML model file '{info['name']}' not found!")
                print(f"   Path checked: {model_path}")
                print(
                    f"   Image-based predictions for '{model_type}' will fail at runtime."
                )
                print("=======================================================\n")
