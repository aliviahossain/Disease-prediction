from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from backend import db, bcrypt
from backend.models.user import User
from flask import session

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/auth', methods=['GET'])
def auth():
    # Deprecated: Redirect to login or profile
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))
    return redirect(url_for('auth.login', tab=request.args.get('tab', 'signin')))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('auth.profile')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login', tab='signin')) # Keep on login page
            
    # GET request: render auth template
    active_tab = request.args.get('tab', 'signin')
    return render_template('auth.html', active_tab=active_tab)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # 1. Reject empty fields
    if not username or not email or not password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    # 2. Check for existing user (split for better internal logging if needed, but flash user-friendly)
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'danger')
        return redirect(url_for('auth.login', tab='register'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already taken.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash('Account Created Successfully. Please Sign In.', 'success')
    # Redirect to signin tab after successful registration
    return redirect(url_for('auth.login', tab='signin'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    # handle form update logic here
    return redirect(url_for('auth.profile'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

