from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Branch, Division
from app.services.auth_service import (
    build_signup_user,
    friendly_signup_integrity_error,
    normalize_signup_data,
    validate_signup_data,
)

auth_bp = Blueprint('auth', __name__)


def render_signup(form_data=None):
    return render_template(
        'auth/signup.html',
        branches=Branch.query.order_by(Branch.name.asc()).all(),
        divisions=Division.query.order_by(Division.name.asc()).all(),
        form_data=form_data or {},
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(role_redirect(current_user.role))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')
        role = request.form.get('role')
        user = User.query.filter_by(email=email, role=role).first()

        if user and user.check_password(password):
            if not user.verified:
                flash("Your account is pending verification.", "warning")
                return redirect(url_for('auth.login'))
            login_user(user)
            return redirect(role_redirect(user.role))
        else:
            flash("Invalid credentials or role mismatch.", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        form_data = normalize_signup_data(request.form)
        errors, branch, division = validate_signup_data(form_data)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_signup(form_data=form_data)

        new_user = build_signup_user(form_data, branch=branch, division=division)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            flash(friendly_signup_integrity_error(error), "danger")
            return render_signup(form_data=form_data)

        flash("Signup successful! Please wait for verification.", "success")
        return redirect(url_for('auth.login'))

    return render_signup()

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))

def role_redirect(role):
    if role == 'admin':
        return url_for('admin.dashboard')
    elif role == 'hod':
        return url_for('hod.dashboard')
    elif role == 'faculty':
        return url_for('faculty.dashboard')
    elif role == 'student':
        return url_for('student.dashboard')
    return url_for('auth.login')
