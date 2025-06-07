"""
# ---------------------------------------------------------------------
# auth.py
# app/views/auth.py
# Authentication and account bootstrap views and routes for Grylli.
# ---------------------------------------------------------------------
"""

import time
from functools import wraps
from urllib.parse import parse_qs, unquote, urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import _  # ✅ i18n support
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.forms.admin_creation_form import AdminCreationForm
from app.forms.auth_form import ForgotPasswordForm, ForgotUsernameForm
from app.forms.login_form import LoginForm
from app.forms.signup_form import SignupForm  # <-- New signup form import
from app.models import User, db
from app.services.settings import get_setting  # <-- Needed for signup PIN retrieval
from app.services.system_settings_email import send_email
from app.utils.logging import log_error_message, log_info_message
from app.utils.rate_limit import get_delay_seconds, record_failure, reset_failures

bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------
# BOOTSTRAP: First-time admin setup
# ---------------------------------------------------------------------
@bp.route("/bootstrap", methods=["GET", "POST"])
def bootstrap():
    """
    View: First-time admin setup (bootstrap)
    ======================================

    Only accessible when no admin account exists in the database.

    GET:
        Displays the admin creation form.

    POST:
        Validates the form and creates the admin user if the form is valid.
        Redirects to the login page on success. If any error occurs, an error
        flash message is displayed and the form is rendered again.

    :returns: Redirects to the login page on success or renders the bootstrap
        template on GET or form errors.
    """
    try:
        admin_count = db.session.query(User).filter_by(role="admin").count()
        if admin_count > 0:
            log_info_message("Admin account already exists. Redirecting to login.")
            return redirect(url_for("auth.login"))
    except Exception as e:
        log_error_message("Database error during bootstrap admin check: " + str(e))
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
                role="admin",
                is_enabled=True,
            )
            db.session.add(new_user)
            db.session.commit()

            log_info_message(
                "Admin account '%(username)s' created during bootstrap." % {"username": username}
            )
            flash(_("Admin account created successfully."), "success")

            user = User.query.filter_by(username=username).first()

            login_user(user)
            session.permanent = True
            log_info_message(
                "User %(user)s logged in with ID %(id)s" % {"user": user.username, "id": user.id}
            )

            return redirect(url_for("index.index"))
        except Exception as e:
            log_error_message("Error creating admin during bootstrap: " + str(e))
            flash(_("An error occurred while creating the admin account."), "danger")

    return render_template("auth/bootstrap.html", form=form)


# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------
@bp.route("/login/", methods=["GET", "POST"])
def login():
    """
    View: Login
    Handles user login requests, authenticating users via username and password.
    """

    if current_user.is_authenticated:
        return redirect(url_for("index.index"))

    if request.method == "GET":
        session.pop("pending_mfa_user_id", None)
        session.pop("pending_mfa_next", None)

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()

        user = User.query.filter_by(username=username).first()

        if user:
            if not user.is_enabled:
                flash(
                    _(
                        "Your account is not activated. Please check your email for the activation link."
                    ),
                    "warning",
                )
                return render_template("auth/login.html", form=form)

            if check_password_hash(user.password_hash, form.password.data):
                reset_failures(username)

                if getattr(user, "mfa_enabled", False):
                    session["pending_mfa_user_id"] = user.id
                    raw_next = request.args.get("next")
                    next_page = unquote(raw_next) if raw_next else None
                    if next_page:
                        session["pending_mfa_next"] = next_page
                    flash(
                        _("Multi-factor authentication required. Please enter your code."), "info"
                    )
                    return redirect(url_for("mfa.mfa_challenge"))

                login_user(user)
                flash(_("Logged in successfully."), "success")
                log_info_message(f"✅ Login successful for user: {username}")
                raw_next = request.args.get("next")
                next_page = unquote(raw_next) if raw_next else None
                if next_page and urlparse(next_page).netloc == "":
                    return redirect(next_page)
                return redirect(url_for("index.index"))

        # --- Login failed: record failure first ---
        record_failure(username)

        # --- Then immediately check for delay ---
        delay = round(get_delay_seconds(username))
        if delay > 0:
            log_info_message(f"Redirecting to rate-limit page for '{username}' with delay={delay}s")
            return redirect(url_for("auth.rate_limit_delay", username=username))

        flash(_("Invalid username or password."), "danger")
        log_error_message(f"❌ Failed login attempt for user: {username}")

    if request.method == "POST" and form.errors:
        log_error_message(f"Login form validation errors: {form.errors}")

    return render_template("auth/login.html", form=form)


# ---------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------
@bp.route("/logout/")
@login_required
def logout():
    """
    View: Logout
    =======

    Logs the user out and redirects to the login page.

    :returns: Redirects to the login page.
    """
    logout_user()
    flash(_("You have been logged out."), "success")
    username = current_user.username if current_user.is_authenticated else "Anonymous"
    log_info_message(f"User '{username}' logged out.")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------
# ADMIN REQUIRED
# ---------------------------------------------------------------------
def admin_required(view_func):
    """
    Decorator that ensures a user is authenticated and has an "admin" role
    before allowing access to the decorated view function. If the user is
    not authenticated or does not have the "admin" role, they are redirected
    to the index page with an "Access denied" message.

    :param view_func: The view function to be wrapped
    :type view_func: function
    :returns: The wrapped view function if the user is authorized, otherwise
              redirects to the index page
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function that checks if the user is authenticated and has
        the "admin" role before allowing access to the decorated view function.
        If the user is not authenticated or does not have the "admin" role,
        they are redirected to the index page with an "Access denied" message.

        :param view_func: The view function to be wrapped
        :type view_func: function
        :returns: The wrapped view function if the user is authorized, otherwise
                  redirects to the index page
        """
        if not current_user.is_authenticated or current_user.role != "admin":
            flash(_("Access denied."), "danger")
            return redirect(url_for("index.index"))
        return view_func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------
# Forgot username
# ---------------------------------------------------------------------
@bp.route("/forgot-username", methods=["GET", "POST"])
def forgot_username():
    """
    View: Forgot Username

    Allows users to request an email be sent to them with their username.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))

    form = ForgotUsernameForm()
    if form.cancel.data:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            send_email(
                to=email,
                subject="Your Username",
                body=f"Hello,\n\nYour username is: {user.username}\n\n- Grylli Team",
            )
            log_info_message(f"Username reminder sent to '{user.email}'.")
        flash(_("If a user with that email exists, we've sent the username to them."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_username.html", form=form)

    return render_template("auth/forgot_username.html", form=form)


# ---------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------
@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # If already logged in, send to dashboard (or home)
    """
    View: Forgot Password
    ==============

    Allows users to request a password reset email be sent to them.

    :returns: Redirects to the login page on success, renders the forgot password
              template on failure.

    """
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    form = ForgotPasswordForm()
    # Check if cancel was pressed before validate_on_submit!
    if form.cancel.data:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.email.lower() == form.email.data.strip().lower():
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_email(
                to=user.email,
                subject="Reset Your Password",
                body=f"Hello {user.username},\n\nClick below to reset your password:\n{reset_url}\n\nThis link will expire in 10 minutes.\n\n- Grylli Team",
            )
            flash(_("A password reset link has been sent to your email."), "success")
            log_info_message(
                f"Password reset email sent to '{user.email}' for username '{user.username}'."
            )
        else:
            flash(_("No account found matching that username and email."), "danger")
            log_error_message("Password reset attempted with unknown username/email.")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


# ---------------------------------------------------------------------
# Generate token
# ---------------------------------------------------------------------
def generate_reset_token(email):
    """
    Generates a URL-safe token for password reset purposes.

    :param email: The user's email address
    :type email: str
    :returns: A URL-safe token that can be used for password reset
    :rtype: str
    """

    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="reset-password")


# ---------------------------------------------------------------------
# Reset token
# ---------------------------------------------------------------------
def verify_reset_token(token, max_age=None):
    """
    Verifies a password reset token and retrieves the associated email.

    :param token: The token to be verified
    :type token: str
    :param max_age: Maximum age of the token in seconds (optional)
    :type max_age: int or None
    :returns: The email address associated with the token if valid, else None
    :rtype: str or None
    """

    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    if max_age is None:
        max_age = current_app.config["TOKEN_EXPIRATION_SECONDS"]
    try:
        return s.loads(token, salt="reset-password", max_age=max_age)
    except Exception:
        return None


# ---------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------
@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Handles password reset form submission.

    Verifies the password reset token and, if valid, displays a form for the user to enter their new password.
    If the form is submitted with valid data, the user's password is updated and they are redirected to the login page.
    If the form is invalid or the token is invalid/expired, the user is redirected to the login page with an error message.

    :param token: The password reset token
    :type token: str
    :returns: A rendered template or redirect response
    :rtype: Response
    """
    from app.forms.reset_password_form import ResetPasswordForm

    email_from_token = verify_reset_token(token)
    if not email_from_token:
        log_error_message("Reset link invalid or expired.")
        flash(_("The reset link is invalid or has expired."), "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()

    # --- Cancel button logic ---
    if form.cancel.data or "cancel" in request.form:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if not user or user.email.lower() != form.email.data.strip().lower():
            flash(_("Username and email do not match."), "danger")
            return redirect(url_for("auth.reset_password", token=token))

        # Update password
        user.password_hash = generate_password_hash(form.password.data.strip())
        db.session.commit()

        log_info_message(f"User '{user.username}' reset their password via token.")

        send_email(
            to=user.email,
            subject="Your Grylli Password Was Changed",
            body=f"""Hello {user.username},

        Your password was successfully changed. If you did not perform this action, please reset it immediately or contact support.

        - Grylli Team
        """,
        )

        flash(_("Your password has been reset. Please log in."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


# ---------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------
@bp.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Handles new user registration (signup).
    """

    if current_user.is_authenticated:
        return redirect(url_for("index.index"))

    form = SignupForm()
    signup_code = get_setting("SIGNUP_CODE", decrypt_value=True)

    # --- Cancel button logic ---
    if form.cancel.data or "cancel" in request.form:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        email_key = form.email.data.strip().lower()
        delay = get_delay_seconds(email_key)
        if delay > 0:
            log_info_message(f"Redirecting to rate-limit page for signup email '{email_key}'")
            return redirect(
                url_for("auth.rate_limit_delay", username=email_key)
            )  # Username param reused

        # Check registration PIN matches the secret code
        if form.registration_pin.data.strip() != signup_code:
            record_failure(email_key)
            flash(_("Invalid registration PIN."), "danger")
            log_error_message("Invalid registration PIN entered during signup.")
            return render_template("auth/signup.html", form=form)

        # Check if username or email already exists
        if User.query.filter(
            (User.username == form.username.data) | (User.email == email_key)
        ).first():
            record_failure(email_key)
            flash(_("Username or email already exists."), "danger")
            return render_template("auth/signup.html", form=form)

        # Create new user (inactive)
        new_user = User(
            username=form.username.data.strip(),
            email=email_key,
            password_hash=generate_password_hash(form.password.data.strip()),
            role="user",
            is_enabled=False,
        )
        db.session.add(new_user)
        db.session.commit()

        log_info_message(f"New user '{new_user.username}' registered via signup.")
        reset_failures(email_key)

        # Generate activation token
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps(new_user.email, salt="account-activation")

        activation_url = url_for("auth.activate_account", token=token, _external=True)

        send_email(
            to=new_user.email,
            subject=_("Activate Your Grylli Account"),
            body=_("Hello {username},\n\nPlease activate your account by clicking...").format(
                username=new_user.username
            ),
        )

        flash(_("Account created! Please check your email to activate your account."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html", form=form)


# ---------------------------------------------------------------------
# Account Activation
# ---------------------------------------------------------------------
@bp.route("/activate-account/<token>")
def activate_account(token):
    """
    Activate a user's account via a valid activation token.

    :param token: the activation token sent to the user via email
    :return: redirect to login page with success or error message
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(
            token, salt="account-activation", max_age=current_app.config["TOKEN_EXPIRATION_SECONDS"]
        )  # 10 min expiry
    except Exception:
        flash(_("Activation link is invalid or expired."), "danger")
        log_error_message("Activation token expired or invalid.")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        log_error_message("User not found.")
        flash(_("User not found."), "danger")
        return redirect(url_for("auth.signup"))

    if user.is_enabled:
        flash(_("Account already activated. Please log in."), "info")
        return redirect(url_for("auth.login"))

    user.is_enabled = True
    db.session.commit()

    log_info_message(f"User '{user.username}' activated their account.")

    flash(_("Your account has been activated! You can now log in."), "success")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------
# RATE LIMIT DELAY PAGE
# ---------------------------------------------------------------------
@bp.route("/rate-limit/<username>")
def rate_limit_delay(username):
    """
    Show a temporary rate-limit screen and redirect back to login
    after the required cooldown period.
    """
    from app.utils.rate_limit import get_delay_seconds

    delay = round(get_delay_seconds(username))
    log_info_message(f"Rate limit delay for '{username}' is {delay} seconds.")
    return render_template("auth/rate_limit.html", delay=delay)
