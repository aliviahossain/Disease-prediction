from backend import create_app

# This creates the 'app' variable that Gunicorn needs to import
app = create_app()

# This block only runs when you execute "python run.py"
# It is skipped by Gunicorn
if __name__ == "__main__":
    app.run(debug=True, port=5000)