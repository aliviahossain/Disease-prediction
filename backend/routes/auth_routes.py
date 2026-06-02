import re
from datetime import date, datetime
from urllib.parse import urljoin, urlparse

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import OperationalError

from backend import bcrypt, db
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)

PHONE_RE = re.compile(r"^\+[1-9][0-9]{7,14}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{1,79}$")
RELATION_RE = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{1,49}$")
ADDRESS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s,.'/#-]{4,159}$")
MEDICAL_TEXT_RE = re.compile(r"^[A-Za-z][A-Za-z\s,.';:/()&+-]*$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
ALLOWED_GENDERS = {"Male", "Female", "Other", ""}
MAX_PROFILE_AGE = 120


def _clean_form_value(name):
    return (request.form.get(name) or "").strip()


def _form_has_field(name):
    """True when the field was included in the POST (disabled inputs are omitted)."""
    return name in request.form


def _validate_phone(value, label, errors):
    if not value:
        return None

    if not PHONE_RE.fullmatch(value):
        errors.append(
            f"{label} must start with a country code plus sign and contain digits only."
        )
        return None
    return value


def _validate_pattern(value, pattern, label, errors, message):
    if not value:
        return None
    if not pattern.fullmatch(value):
        errors.append(f"{label} {message}")
        return None
    return value


def _validate_dob(value, errors):
    dob_day = _clean_form_value("dob_day")
    dob_month = _clean_form_value("dob_month")
    dob_year = _clean_form_value("dob_year")
    has_dropdown_dob = any([dob_day, dob_month, dob_year])

    if has_dropdown_dob:
        if not all([dob_day, dob_month, dob_year]):
            errors.append("Date of birth requires day, month, and year.")
            return None

        try:
            parsed = date(int(dob_year), int(dob_month), int(dob_day))
        except ValueError:
            errors.append("Date of birth must be a valid date.")
            return None
    elif value:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date of birth must be a valid date.")
            return None
    else:
        return None

    today = date.today()
    oldest_allowed = _oldest_allowed_dob(today)
    if parsed > today:
        errors.append("Date of birth cannot be in the future.")
        return None
    if parsed < oldest_allowed:
        errors.append(f"Date of birth must be within the last {MAX_PROFILE_AGE} years.")
        return None
    return parsed


def _validate_float(value, label, minimum, maximum, errors):
    if not value:
        return None

    try:
        parsed = float(value)
    except ValueError:
        errors.append(f"{label} must be a number.")
        return None

    if parsed < minimum or parsed > maximum:
        errors.append(f"{label} must be between {minimum:g} and {maximum:g}.")
        return None
    return parsed


def _validate_medical_text(value, label, max_length, errors):
    if not value:
        return None
    if len(value) > max_length:
        errors.append(f"{label} must be {max_length} characters or fewer.")
        return None
    if not MEDICAL_TEXT_RE.fullmatch(value):
        errors.append(f"{label} must contain text only. Numbers are not allowed.")
        return None
    return value


def _profile_dob_bounds():
    today = date.today()
    return _oldest_allowed_dob(today).isoformat(), today.isoformat()


def _dob_year_options():
    today = date.today()
    oldest_allowed = _oldest_allowed_dob(today)
    return range(today.year, oldest_allowed.year - 1, -1)


def _oldest_allowed_dob(today):
    try:
        return today.replace(year=today.year - MAX_PROFILE_AGE)
    except ValueError:
        return today.replace(year=today.year - MAX_PROFILE_AGE, day=28)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/auth", methods=["GET"])
def auth():
    # Deprecated: Redirect to login or profile
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))
    return redirect(url_for("auth.login", tab=request.args.get("tab", "signin")))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            session.permanent = True  # Enforce PERMANENT_SESSION_LIFETIME (2h)
            flash("Login successful!", "success")
            next_page = request.args.get("next")
            if not next_page or not is_safe_url(next_page):
                next_page = url_for("auth.profile")
            return redirect(next_page)

        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for("auth.login", tab="signin"))  # Keep on login page

    # GET request: render auth template
    active_tab = request.args.get("tab", "signin")
    return render_template("auth.html", active_tab=active_tab)



MIN_PASSWORD_LEN = 8
MAX_USERNAME_LEN = 20  

@auth_bp.route('/signup', methods=['POST'])
def signup():
    username = (request.form.get('username') or '').strip()
    email    = (request.form.get('email')    or '').strip()
    password =  request.form.get('password') or ''

    # 1. Reject empty fields
    if not username or not email or not password:
        flash("All fields are required.", "danger")
        return redirect(url_for("auth.login", tab="register"))

    # 2. Validate username length (DB column is String(20))
    if len(username) > MAX_USERNAME_LEN:
        flash(f'Username must be {MAX_USERNAME_LEN} characters or fewer.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    # 2. Validate email format
    if not EMAIL_RE.fullmatch(email):
        flash('Invalid email address format.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    # 3. Validate password strength
    if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        flash('Password must be at least 8 characters long, contain at least one number and one special character.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    # 2. Check for existing user (split for better internal logging if needed, but flash user-friendly)
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'danger')
        return redirect(url_for('auth.login', tab='register'))

    if User.query.filter_by(username=username).first():
        flash("Username already taken.", "danger")
        return redirect(url_for("auth.login", tab="register"))

    # Hash password and create user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash('Account Created Successfully. Please Sign In.', 'success')
    return redirect(url_for('auth.login', tab='signin'))

@auth_bp.route("/profile")
@login_required
def profile():
    dob_min, dob_max = _profile_dob_bounds()
    return render_template(
        "profile.html",
        user=current_user,
        dob_min=dob_min,
        dob_max=dob_max,
        day_options=range(1, 32),
        month_options=range(1, 13),
        year_options=_dob_year_options(),
        height_options=range(30, 273),
        weight_options=range(1, 636),
    )


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    errors = []
    phone = emergency_phone = address = emergency_name = emergency_relation = None
    dob = height = weight = allergies = medical_notes = None
    gender = current_user.gender

    if _form_has_field("phone"):
        phone = _validate_phone(_clean_form_value("phone"), "Phone", errors)
    if _form_has_field("emergency_phone"):
        emergency_phone = _validate_phone(
            _clean_form_value("emergency_phone"), "Emergency phone", errors
        )
    if _form_has_field("address"):
        address = _validate_pattern(
            _clean_form_value("address"),
            ADDRESS_RE,
            "Address",
            errors,
            "must be 5 to 160 characters and contain only letters, numbers, spaces, and common address punctuation.",
        )
    if _form_has_field("emergency_name"):
        emergency_name = _validate_pattern(
            _clean_form_value("emergency_name"),
            NAME_RE,
            "Emergency contact name",
            errors,
            "must contain only letters, spaces, apostrophes, periods, or hyphens.",
        )
    if _form_has_field("emergency_relation"):
        emergency_relation = _validate_pattern(
            _clean_form_value("emergency_relation"),
            RELATION_RE,
            "Emergency relation",
            errors,
            "must contain only letters, spaces, apostrophes, periods, or hyphens.",
        )
    if any(_form_has_field(name) for name in ("dob_day", "dob_month", "dob_year", "dob")):
        dob = _validate_dob(_clean_form_value("dob"), errors)
    if _form_has_field("gender"):
        gender = _clean_form_value("gender")
        if gender not in ALLOWED_GENDERS:
            errors.append("Gender must be Male, Female, or Other.")
    if _form_has_field("height"):
        height = _validate_float(_clean_form_value("height"), "Height", 30, 272, errors)
    if _form_has_field("weight"):
        weight = _validate_float(_clean_form_value("weight"), "Weight", 1, 635, errors)
    if _form_has_field("allergies"):
        allergies = _validate_medical_text(
            _clean_form_value("allergies"), "Allergies", 200, errors
        )
    if _form_has_field("medical_notes"):
        medical_notes = _validate_medical_text(
            _clean_form_value("medical_notes"), "Medical notes", 1000, errors
        )

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("auth.profile"))

    if _form_has_field("phone"):
        current_user.phone = phone
    if _form_has_field("address"):
        current_user.address = address
    if _form_has_field("emergency_name"):
        current_user.emergency_name = emergency_name
    if _form_has_field("emergency_relation"):
        current_user.emergency_relation = emergency_relation
    if _form_has_field("emergency_phone"):
        current_user.emergency_phone = emergency_phone
    if any(_form_has_field(name) for name in ("dob_day", "dob_month", "dob_year", "dob")):
        current_user.dob = dob
    if _form_has_field("gender"):
        current_user.gender = gender or None
    if _form_has_field("height"):
        current_user.height = height
    if _form_has_field("weight"):
        current_user.weight = weight
    
    # Recompute BMI if height or weight were sent/updated in this request
    if _form_has_field("height") or _form_has_field("weight"):
        h = current_user.height
        w = current_user.weight
        current_user.bmi = round(w / ((h / 100) ** 2), 2) if h and w else None

    if _form_has_field("allergies"):
        current_user.allergies = allergies or None
    if _form_has_field("medical_notes"):
        current_user.medical_notes = medical_notes or None
    try:
        db.session.commit()
    except OperationalError as error:
        db.session.rollback()
        if "readonly database" in str(error).lower():
            flash(
                "Profile could not be saved because the local database is read-only. "
                "Please restart the Flask server and check database file permissions.",
                "danger",
            )
            return redirect(url_for("auth.profile"))
        raise

    flash("Profile updated successfully.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
