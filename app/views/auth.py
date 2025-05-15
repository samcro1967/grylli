# ---------------------------------------------------------------------
# auth.py
# Authentication and first-time bootstrap views for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms.admin_creation_form import AdminCreationForm
from app.db import get_db
from app.utils.logging import log_info_message, log_error_message
from app.models import User
from app.forms.login_form import LoginForm

bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------------------------------------------------------------
# BOOTSTRAP: First-time admin setup
# ---------------------------------------------------------------------

@bp.route("/bootstrap/", methods=["GET", "POST"])
def bootstrap():
    db = get_db()

    try:
        result = db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()
        if result[0] > 0:
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

            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                (username, password_hash)
            )
            db.commit()

            log_info_message(f"Admin account '{username}' created during bootstrap.")
            flash("Admin account created successfully.", "success")

            # Load the user object after creation (you need to implement this)
            from app.models import User
            user = User.get_by_username(db, username)  # Implement get_by_username method

            # Log the user in
            login_user(user)
            log_info_message(f"User {user.username} logged in with ID {user.id}")

            return redirect(url_for("index.index"))
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
        db = get_db()
        user = User.get_by_username(db, form.username.data.strip())

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get('next')
            # Security check for next page
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index.index')
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
    return redirect(url_for('auth.login'))