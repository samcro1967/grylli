"""
# ---------------------------------------------------------------------
# auth.py
# app/views/auth.py
# Authentication and account bootstrap views and routes for Grylli.
# ---------------------------------------------------------------------
"""

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
    ========

    GET:
        Displays the login form.

    POST:
        Validates the form and logs the user in if the form is valid.
        Redirects to the "next" URL if provided in the query string, or to the
        index page if no "next" is given. If any error occurs, an error flash
        message is displayed and the form is rendered again.

    :returns: Redirects to the "next" URL or the index page on success, or renders
        the login template on GET or form errors.
    """
    # If already logged in, send to dashboard (or home)
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))

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
                login_user(user)
                flash(_("Logged in successfully."), "success")
                log_info_message(
                    "✅ Login successful for user: {username}".format(username=username)
                )

                raw_next = request.args.get("next")
                next_page = unquote(raw_next) if raw_next else None

                # Validate: only redirect to internal URLs
                if next_page and urlparse(next_page).netloc == "":
                    return redirect(next_page)
                else:
                    return redirect(url_for("index.index"))

        # Invalid login
        flash(_("Invalid username or password."), "danger")
        log_error_message("Failed login attempt for user: {username}".format(username=username))

    # Log form errors
    if request.method == "POST" and form.errors:
        log_error_message("Login form validation errors: {errors}".format(errors=form.errors))

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
    # If already logged in, send to dashboard (or home)
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    form = ForgotUsernameForm()
    if form.cancel.data:
        return redirect(url_for("auth.login"))
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            send_email(
                to=form.email.data.strip(),
                subject="Your Username",
                body=f"Hello,\n\nYour username is: {user.username}\n\n- Grylli Team",
            )
        flash(_("If a user with that email exists, we've sent the username to them."), "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_username.html", form=form)


# ---------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------
@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # If already logged in, send to dashboard (or home)
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
        else:
            flash(_("No account found matching that username and email."), "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


# ---------------------------------------------------------------------
# Generate token
# ---------------------------------------------------------------------
def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="reset-password")


# ---------------------------------------------------------------------
# Reset token
# ---------------------------------------------------------------------
def verify_reset_token(token, max_age=None):
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
    from app.forms.reset_password_form import ResetPasswordForm

    email_from_token = verify_reset_token(token)
    if not email_from_token:
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
    # If already logged in, send to dashboard (or home)
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    form = SignupForm()
    signup_code = get_setting("SIGNUP_CODE", decrypt_value=True)

    # --- Cancel button logic ---
    if form.cancel.data or "cancel" in request.form:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        # Check registration PIN matches the secret code
        if form.registration_pin.data.strip() != signup_code:
            flash(_("Invalid registration PIN."), "danger")
            return render_template("auth/signup.html", form=form)

        # Check if username or email already exists
        if User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first():
            flash(_("Username or email already exists."), "danger")
            return render_template("auth/signup.html", form=form)

        # Create new user (inactive)
        new_user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            password_hash=generate_password_hash(form.password.data.strip()),
            role="user",
            is_enabled=False,
        )
        db.session.add(new_user)
        db.session.commit()

        # Generate activation token
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = s.dumps(new_user.email, salt="account-activation")

        activation_url = url_for("auth.activate_account", token=token, _external=True)

        # Send activation email
        send_email(
            to=new_user.email,
            subject="Activate Your Grylli Account",
            body=f"Hello {new_user.username},\n\nPlease activate your account by clicking the link below:\n\n{activation_url}\n\nThis link will expire in 10 minutes.\n\n- Grylli Team",
        )

        flash(_("Account created! Please check your email to activate your account."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html", form=form)


# ---------------------------------------------------------------------
# Account Activation
# ---------------------------------------------------------------------
@bp.route("/activate-account/<token>")
def activate_account(token):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(
            token, salt="account-activation", max_age=current_app.config["TOKEN_EXPIRATION_SECONDS"]
        )  # 10 min expiry
    except Exception:
        flash(_("Activation link is invalid or expired."), "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash(_("User not found."), "danger")
        return redirect(url_for("auth.signup"))

    if user.is_enabled:
        flash(_("Account already activated. Please log in."), "info")
        return redirect(url_for("auth.login"))

    user.is_enabled = True
    db.session.commit()

    flash(_("Your account has been activated! You can now log in."), "success")
    return redirect(url_for("auth.login"))
