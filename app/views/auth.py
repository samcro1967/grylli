# ---------------------------------------------------------------------
# auth.py
# Authentication and first-time bootstrap views for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user
from werkzeug.security import generate_password_hash
from app.forms.admin_creation_form import AdminCreationForm
from app.db import get_db
from app.utils.logging import log_info_message, log_error_message

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

            return redirect(url_for("index.index"))
        except Exception as e:
            log_error_message(f"Error creating admin during bootstrap: {e}")
            flash("An error occurred while creating the admin account.", "danger")

    return render_template("auth/bootstrap.html", form=form)

# ---------------------------------------------------------------------
# LOGIN: Placeholder for login view
# ---------------------------------------------------------------------

@bp.route("/login/", methods=["GET", "POST"])
def login():
    """
    Placeholder login route for compatibility with post-bootstrap redirect.

    Returns:
        Renders a temporary message or login screen once implemented.
    """
    return render_template("auth/login.html")