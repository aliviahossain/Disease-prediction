from backend import create_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create Flask app using the factory function
app = create_app()

# For Gunicorn or other WSGI servers
# Gunicorn will use "app" automatically.

if __name__ == "__main__":
    # Run locally for development
    print("\n" + "="*50)
    print("Starting Flask Development Server")
    print("="*50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5001)