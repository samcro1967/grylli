# ---------------------------------------------------------------------
# auth.py
# Authentication and first-time bootstrap views for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
    """
    Handles initial admin account creation if no admins exist.

    This view is only accessible when no admin users are present in the database.
    If an admin exists, the user is redirected to the login page.
    On valid submission, a new admin is created and redirected to login.

    Returns:
        - Redirect to /auth/login on success or if admin already exists.
        - Renders the bootstrap form on GET or validation failure.
    """
    db = get_db()

    try:
        # Check if any admin already exists
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
                (form.username.data.strip(), password_hash)
            )

            db.commit()

            log_info_message(f"Admin account '{username}' created during bootstrap.")
            flash("Admin account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
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
