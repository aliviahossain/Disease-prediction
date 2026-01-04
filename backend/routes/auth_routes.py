from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from backend import db, bcrypt
from backend.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth', methods=['GET'])
def auth():
    # If already logged in, redirect to profile
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))
    
    # Get active tab from query parameter, default to 'signin'
    active_tab = request.args.get('tab', 'signin')
    return render_template('auth.html', active_tab=active_tab)

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        session.clear() # Good practice to rotate/clear old session data
        session['user_id'] = user.id
        flash('Login successful!', 'success')
        return redirect(url_for('auth.profile'))
    else:
        # 1. Generic error message
        flash('Invalid email or password', 'danger')
        return redirect(url_for('auth.auth', tab='signin'))

@auth_bp.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # 1. Reject empty fields
    if not username or not email or not password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('auth.auth', tab='register'))

    # 2. Check for existing user (split for better internal logging if needed, but flash user-friendly)
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'danger')
        return redirect(url_for('auth.auth', tab='register'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already taken.', 'danger')
        return redirect(url_for('auth.auth', tab='register'))

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash('Account Created Successfully. Please Sign In.', 'success')
    # Redirect to signin tab after successful registration
    return redirect(url_for('auth.auth', tab='signin'))

@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.auth'))
    
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.auth'))

