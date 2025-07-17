"""
# ---------------------------------------------------------------------
# auth.py
# app/views/auth.py
# Authentication and account bootstrap views and routes for Grylli.
# ---------------------------------------------------------------------
"""

import time
from datetime import datetime, timedelta, timezone
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
    abort,
)
from flask_babel import _  #  i18n support
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.forms.admin_creation_form import AdminCreationForm
from app.forms.auth_form import ForgotPasswordForm, ForgotUsernameForm
from app.forms.login_form import LoginForm
from app.forms.security_questions_form import SecurityQuestionsForm
from app.forms.signup_form import SignupForm  # <-- New signup form import
from app.models import User, db
from app.services.security_questions import (
    find_user_by_identifier,
    user_has_security_questions,
    verify_security_answer,
)
from app.services.settings import get_setting  # <-- Needed for signup PIN retrieval
from app.services.system_settings_email import send_email
from app.utils.logging import log_error_message, log_exception_with_traceback, log_info_message, log_debug_message
from app.utils.rate_limit import (
    get_delay_seconds,
    get_failure_count,
    record_failure,
    reset_failures,
)
from app.utils.security import get_safe_redirect
from app.services.auth_helpers import generate_token, verify_token

bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------
# BOOTSTRAP: First-time admin setup
# ---------------------------------------------------------------------
@bp.route("bootstrap", methods=["GET", "POST"], strict_slashes=False)
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
        log_exception_with_traceback("Database error during bootstrap admin check", e)
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
            log_info_message(f"Auth - {username} - Bootstrap admin account created")
            flash(_("Admin account created successfully."), "success")

            user = User.query.filter_by(username=username).first()

            # Check if user account is locked
            if user and user.locked_until and not current_app.config.get("TESTING"):
                locked_until = user.locked_until
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                if locked_until > datetime.now(timezone.utc):
                    flash(
                        _("Your account is temporarily locked. Please try again later."), "danger"
                    )
                    log_info_message(f"Auth - {username} - Attempted login during active lockout")
                    return render_template("auth/login.html", form=form)

            login_user(user)
            session.permanent = True
            log_info_message(f"Auth - {user.username} - Logged in")
            return redirect(url_for("home.index"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Error creating admin during bootstrap", e)
            flash(_("An error occurred while creating the admin account."), "danger")

    return render_template("auth/bootstrap.html", form=form)


# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------
@bp.route("login/", methods=["GET", "POST"], strict_slashes=False)
def login():
    """
    View: Login
    Handles user login requests, authenticating users via username and password.
    """
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "GET":
        session.pop("pending_mfa_user_id", None)
        session.pop("pending_mfa_next", None)

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()

        user = User.query.filter_by(username=username).first()

        #  Test-only hook to force lockout during login
        if current_app.config.get("TEST_FORCE_LOCK") and user:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
            db.session.commit()


        # ----------------------------
        # 1. Account lockout check
        # ----------------------------
        if user and user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > datetime.now(timezone.utc):
                flash(_("Your account is temporarily locked. Please try again later."), "danger")
                log_info_message(f"Auth - {username} - Attempted login during active lockout")
                return render_template("auth/login.html", form=form)

        # ----------------------------
        # 2. Password check
        # ----------------------------
        if user and check_password_hash(user.password_hash, form.password.data):
            # Clear lockout and reset failures on success
            user.locked_until = None
            db.session.commit()
            reset_failures(username)

            if not user.is_enabled:
                flash(_("Your account is not activated."), "warning")
                return render_template("auth/login.html", form=form)

            if getattr(user, "mfa_enabled", False):
                session["pending_mfa_user_id"] = user.id
                next_page = unquote(request.args.get("next", ""))
                if next_page:
                    session["pending_mfa_next"] = next_page
                flash(_("Multi-factor authentication required."), "info")
                return redirect(url_for("mfa.mfa_challenge"))

            login_user(user)
            flash(_("Logged in successfully."), "success")
            log_info_message(f"Auth - {username} - Logged in")
            next_page = unquote(request.args.get("next", ""))
            next_page = unquote(request.args.get("next", ""))
            # Safe redirect: `get_safe_redirect` ensures `next_page` is same-origin or internal
            return redirect(get_safe_redirect(next_page, fallback_endpoint="home.index"))

        # ----------------------------
        # 3. Record failure
        # ----------------------------
        record_failure(username)
        attempts = get_failure_count(username)

        # Lock account after 10 failures
        if user and attempts >= 10:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            flash(
                _("Too many failed login attempts. Your account is locked for 15 minutes."),
                "danger",
            )
            log_info_message(f"Auth - {username} - Locked out after {attempts} failed attempts")
            return render_template("auth/login.html", form=form)

        # ----------------------------
        # 4. Rate limiting
        # ----------------------------
        delay = round(get_delay_seconds(username))
        if delay > 0:
            log_info_message(f"Auth - {username} - Rate limited with delay {delay}s")
            return redirect(url_for("auth.rate_limit_delay", username=username))


        # ----------------------------
        # 5. Invalid login fallback
        # ----------------------------
        flash(_("Invalid username or password."), "danger")
        log_info_message(f"Auth - {username} - Failed login attempt")

    if request.method == "POST" and form.errors:
        username = (form.username.data or "").strip()
        log_info_message(f"Auth - {username} - Login form validation error")

    return render_template("auth/login.html", form=form)


# ---------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------
@bp.route("logout/", strict_slashes=False)
@login_required
def logout():
    """
    View: Logout
    =======

    Logs the user out and redirects to the login page.

    :returns: Redirects to the login page.
    """
    username = current_user.username  # Save before logout
    logout_user()
    flash(_("You have been logged out."), "success")
    log_info_message(f"Auth - {username} - Logged out")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------
# ADMIN REQUIRED
# ---------------------------------------------------------------------
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return abort(403)
        return view_func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------
# Forgot username
# ---------------------------------------------------------------------
@bp.route("forgot-username", methods=["GET", "POST"], strict_slashes=False)
def forgot_username():
    """
    View: Forgot Username

    Allows users to request an email be sent to them with their username.
    """
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    form = ForgotUsernameForm()

    if form.cancel.data:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Step 1: Rate limit check
        delay = get_delay_seconds(email)
        if delay > 0:
            log_info_message(
                f"Redirecting to rate-limit page for forgot-username email '{email}' with delay={delay}s"
            )
            return redirect(url_for("auth.rate_limit_delay", username=email))  # email used as key

        try:
            user = User.query.filter_by(email=email).first()
            if user:
                send_email(
                    to=email,
                    subject="Your Username",
                    body=f"Hello,\n\nYour username is: {user.username}\n\n- Grylli Team",
                )
                reset_failures(email)
                log_info_message(
                    f"Auth - {user.username} - Requested username reminder (sent to {user.email})"
                )
            else:
                record_failure(email)

            flash(
                _("If a user with that email exists, we've sent the username to them."), "success"
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            record_failure(email)
            log_exception_with_traceback("Error during forgot username flow", e)
            flash(_("An error occurred while sending your username reminder."), "danger")

    return render_template("auth/forgot_username.html", form=form)


# ---------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------
@bp.route("forgot-password", methods=["GET", "POST"], strict_slashes=False)
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    form = ForgotPasswordForm()

    # Cancel button
    if form.cancel.data:
        session.pop("reset_user_id", None)
        session.pop("security_questions_shown", None)
        session.pop("reset_attempts", None)
        return redirect(url_for("auth.login"))

    # -------------------------------
    # STEP 1: Email + Username Check
    # -------------------------------
    if not session.get("security_questions_shown"):
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            username = form.username.data.strip()

            # Rate limit before processing
            delay = get_delay_seconds(email)
            if delay > 0:
                log_info_message(
                    f"Redirecting to rate-limit page for forgot-password email '{email}' with delay={delay}s"
                )
                return redirect(url_for("auth.rate_limit_delay", username=email))

            try:
                user = User.query.filter_by(username=username).first()
                if user and user.email.lower() == email:
                    session["reset_user_id"] = user.id
                    session["security_questions_shown"] = True
                    session["reset_attempts"] = 0
                    reset_failures(email)
                    return render_template(
                        "auth/forgot_password.html",
                        form=form,
                        security_questions=user.get_security_questions(),
                    )
                else:
                    record_failure(email)
                    flash(_("No account found matching that username and email."), "danger")
                    log_error_message(
                        f"Password reset attempted with unknown username/email: {username}/{email}"
                    )
            except Exception as e:
                record_failure(email)
                log_exception_with_traceback("Error during forgot password lookup", e)
                flash(_("An error occurred while checking your credentials."), "danger")

        return render_template("auth/forgot_password.html", form=form)

    # -------------------------------
    # STEP 2: Security Questions
    # -------------------------------
    user = db.session.get(User, session.get("reset_user_id"))
    if not user:
        flash(_("Session expired. Please start over."), "warning")
        return redirect(url_for("auth.forgot_password"))

    answers = [
        (form.security_answer_0.data or "").strip(),
        (form.security_answer_1.data or "").strip(),
        (form.security_answer_2.data or "").strip(),
    ]

    # Rate limit check (based on username)
    delay = get_delay_seconds(user.username)
    if delay > 0:
        log_info_message(f"RateLimit - {user.username} - Delay {delay}s on security answers")

        return redirect(url_for("auth.rate_limit_delay", username=user.username))

    session["reset_attempts"] += 1
    if session["reset_attempts"] > 3:
        record_failure(user.username)
        flash(_("Too many failed attempts. Please try again later."), "danger")
        log_error_message(f"Auth - {user.username} - Locked out after failed security answers")
        return redirect(url_for("auth.rate_limit_delay", username=user.username))

    try:
        if current_app.config.get("TEST_FORCE_SECURITY_ERROR"):
            raise Exception("Forced test failure")
        
        if user.verify_security_answers(answers):
            token = generate_token(user.email, salt="reset-password")
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            if current_app.config.get("TEST_FORCE_EMAIL_SEND_ERROR"):
                raise Exception("Simulated email failure")

            send_email(
                to=user.email,
                subject="Reset Your Password",
                body=f"Hello {user.username},\n\nClick below to reset your password:\n{reset_url}",
            )
            reset_failures(user.username)
            flash(_("A password reset link has been sent to your email."), "success")
            log_info_message(
                f"Auth - {user.username} - Requested password reset (sent to {user.email})"
            )

            session.pop("reset_user_id", None)
            session.pop("security_questions_shown", None)
            session.pop("reset_attempts", None)

            return redirect(url_for("auth.login"))

        else:
            record_failure(user.username)
            flash(_("One or more answers were incorrect."), "danger")
            log_info_message(f"Auth - {user.username} - Failed security answers")
            return render_template(
                "auth/forgot_password.html",
                form=form,
                security_questions=user.get_security_questions(),
            )
    except Exception as e:
        record_failure(user.username)
        log_exception_with_traceback("Error during security question validation", e)
        flash(_("An error occurred while verifying your answers."), "danger")
        return render_template("auth/forgot_password.html", form=form)


# ---------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------
@bp.route("reset-password/<token>", methods=["GET", "POST"], strict_slashes=False)
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

    if current_app.config.get("TEST_FORCE_RESET_TOKEN_EMAIL"):
        email_from_token = current_app.config["TEST_FORCE_RESET_TOKEN_EMAIL"]
        log_debug_message(f"Test hook: forced reset token email = {email_from_token}")
    elif current_app.config.get("TEST_SIMULATE_BAD_TOKEN"):
        email_from_token = None
    else:
        email_from_token = verify_token(token, salt="reset-password")

    if not email_from_token:
        log_error_message("Auth - Invalid or expired password reset token")
        flash(_("The reset link is invalid or has expired."), "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()

    # --- Cancel button logic ---
    if form.cancel.data or "cancel" in request.form:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data.strip()).first()
            if not user or user.email.lower() != form.email.data.strip().lower():
                flash(_("Username and email do not match."), "danger")
                return redirect(url_for("auth.reset_password", token=token))

            # Update password
            user.password_hash = generate_password_hash(form.password.data.strip())

            if current_app.config.get("TEST_FORCE_COMMIT_ERROR"):
                raise Exception("Simulated DB commit failure")

            db.session.commit()

            log_info_message(f"Auth - {user.username} - Reset password via token")

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
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Password reset failed", e)
            flash(_("An error occurred while resetting your password."), "danger")

    return render_template("auth/reset_password.html", form=form)


# ---------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------
@bp.route("signup", methods=["GET", "POST"], strict_slashes=False)
def signup():
    """
    Handles new user registration (signup).
    """

    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

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

        try:
            # Check registration PIN matches the secret code
            if form.registration_pin.data.strip() != signup_code:
                record_failure(email_key)
                flash(_("Invalid registration PIN."), "danger")
                log_error_message(f"Auth - {email_key} - Invalid registration PIN during signup")
                return render_template("auth/signup.html", form=form)

            # Check if username or email already exists
            if User.query.filter(
                (User.username == form.username.data) | (User.email == email_key)
            ).first():
                record_failure(email_key)
                flash(_("Username or email already exists."), "danger")
                log_error_message(f"Auth - {email_key} - Signup failed: username or email exists")
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

            log_info_message(f"Auth - {new_user.username} - Registered via signup")
            reset_failures(email_key)

            # Generate activation token
            s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            token = s.dumps(new_user.email, salt="account-activation")

            activation_url = url_for("auth.activate_account", token=token, _external=True)

            if current_app.config.get("TEST_FORCE_EMAIL_SEND_ERROR"):
                raise Exception("Simulated email send failure")

            send_email(
                to=new_user.email,
                subject=_("Activate Your Grylli Account"),
                body=_("Hello {username},\n\nPlease activate your account by clicking...").format(
                    username=new_user.username
                ),
            )

            flash(
                _("Account created! Please check your email to activate your account."), "success"
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Signup failed", e)
            flash(_("An error occurred during signup."), "danger")

    return render_template("auth/signup.html", form=form)


# ---------------------------------------------------------------------
# Account Activation
# ---------------------------------------------------------------------
@bp.route("activate-account/<token>", strict_slashes=False)
def activate_account(token):
    """
    Activate a user's account via a valid activation token.
    """
    if current_app.config.get("TEST_FORCE_ACTIVATION_EMAIL"):
        email = current_app.config["TEST_FORCE_ACTIVATION_EMAIL"]
        log_debug_message(f"Test hook: forced activation email = {email}")
    else:
        email = verify_token(token, salt="account-activation")
        if not email:
            flash(_("Activation link is invalid or expired."), "danger")
            return redirect(url_for("auth.login"))

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            log_error_message("User not found during activation.")
            flash(_("User not found."), "danger")
            return redirect(url_for("auth.signup"))

        if user.is_enabled:
            flash(_("Account already activated. Please log in."), "info")
            return redirect(url_for("auth.login"))

        user.is_enabled = True

        if current_app.config.get("TEST_FORCE_COMMIT_ERROR"):
            raise Exception("Simulated DB commit failure")

        db.session.commit()

        log_info_message(f"Auth - {user.username} - Activated account")
        flash(_("Your account has been activated! You can now log in."), "success")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Account activation failed", e)
        flash(_("Failed to activate account."), "danger")

    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------
# RATE LIMIT DELAY PAGE
# ---------------------------------------------------------------------
@bp.route("rate-limit/<username>", strict_slashes=False)
def rate_limit_delay(username):
    """
    Show a temporary rate-limit screen and redirect back to login
    after the required cooldown period.
    """
    from app.utils.rate_limit import get_delay_seconds

    if current_app.config.get("TEST_FORCE_RATE_LIMIT") and username == "test9999":
        delay = 42
    else:
        delay = round(get_delay_seconds(username))

    log_info_message(f"Auth - {username} - Rate limit delay: {delay} seconds")
    return render_template("auth/rate_limit.html", delay=delay)


# ---------------------------------------------------------------------
# Set security questions
# ---------------------------------------------------------------------
@bp.route("verify_security_question", methods=["GET", "POST"], strict_slashes=False)
def verify_security_question():
    user = find_user_by_identifier(request.args.get("identifier"))
    if not user or not user_has_security_questions(user):
        flash(_("Security questions not set or user not found."), "error")
        return redirect(url_for("auth.forgot_password"))

    form = SecurityQuestionChallengeForm(user=user)
    if form.validate_on_submit():
        if verify_security_answer(user, form):
            token = generate_password_reset_token(user)
            send_password_reset_email(user.email, token)
            flash(_("Password reset email sent."), "info")
            log_info_message(
                f"Auth - {user.username} - Verified security question and sent password reset"
            )
            return redirect(url_for("auth.login"))
        else:
            log_info_message(f"Auth - {user.username} - Failed security question verification")
            flash(_("Incorrect answer."), "error")

    return render_template("auth/verify_security_question.html", form=form)
