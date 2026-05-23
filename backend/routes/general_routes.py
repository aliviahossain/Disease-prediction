from flask import Blueprint, render_template, current_app, redirect, url_for

general_bp = Blueprint(
    'general',
    __name__,
    template_folder='../templates'
)

# Remove the home route since it's handled by disease_bp
# @general_bp.route('/')
# def home():
#     return render_template('main.html')

@general_bp.route('/help')
def help_page():
    return render_template('help.html')

@general_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@general_bp.route('/terms')
def terms():
    return render_template('terms.html')

@general_bp.route('/connect')
def connect():
    return redirect(url_for('disease.contact'))

@general_bp.route('/service-worker.js')
def service_worker():
    return current_app.send_static_file('service-worker.js')

@general_bp.route('/health')
def health_check():
    return {"status": "healthy", "service": "disease-prediction-backend"}, 200

