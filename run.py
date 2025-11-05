from backend import create_app

# Create Flask app using the factory function
app = create_app()

# For Gunicorn or other WSGI servers
# Gunicorn will use "app" automatically.

if __name__ == "__main__":
    # Run locally for development
    app.run(debug=True, host="0.0.0.0", port=5000)
