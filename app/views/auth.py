# ---------------------------------------------------------------------
# auth.py
# Authentication and first-time bootstrap views for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms.admin_creation_form import AdminCreationForm
from app.forms.login_form import LoginForm
from app.utils.logging import log_info_message, log_error_message
from app.models import db, User
from urllib.parse import unquote

bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------
# BOOTSTRAP: First-time admin setup
# ---------------------------------------------------------------------

@bp.route("/bootstrap/", methods=["GET", "POST"])
def bootstrap():
    try:
        admin_count = db.session.query(User).filter_by(role="admin").count()
        if admin_count > 0:
            log_info_message("Admin account already exists. Redirecting to login.")
            return redirect(url_for("auth.login"))
    except Exception as e:
        log_error_message(f"Database error during bootstrap admin check: {e}")
        return "Internal server error", 500

    form = AdminCreationForm()

    if form.validate_on_submit():
        try:
            username = form.username.data.strip()
            password_hash = generate_password_hash(form.password.data)

            new_user = User(
                username=username,
                email=form.email.data.strip(),
                password_hash=password_hash,
                role="admin"
            )
            db.session.add(new_user)
            db.session.commit()

            log_info_message(f"Admin account '{username}' created during bootstrap.")
            flash("Admin account created successfully.", "success")

            user = User.query.filter_by(username=username).first()

            login_user(user)
            log_info_message(f"User {user.username} logged in with ID {user.id}")

            return redirect(url_for("index_bp.index"))
        except Exception as e:
            log_error_message(f"Error creating admin during bootstrap: {e}")
            flash("An error occurred while creating the admin account.", "danger")

    return render_template("auth/bootstrap.html", form=form)

# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------

@bp.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")

            # Always go to the home page after login
            next_page = url_for('index_bp.index')
            return redirect(next_page)

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html", form=form)

# ---------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------
@bp.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")  # ✅ Add this line
    return redirect(url_for('auth.login'))
