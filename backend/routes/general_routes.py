from flask import Blueprint, render_template

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