"""
# ---------------------------------------------------------------------
# users.py
# app/views/users.py
# Admin user management views for Grylli.
# ---------------------------------------------------------------------
"""

from datetime import UTC, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from app.forms.create_user_form import CreateUserForm
from app.forms.edit_user_form import EditUserForm
from app.models import User, db
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required
from app.services.system_settings_email import send_email

bp = Blueprint("users", __name__)


# ---------------------------------------------------------------------
# View: List all users
# ---------------------------------------------------------------------
@bp.route("overview/", strict_slashes=False)
@login_required
@admin_required
def list_users():
    """
    Display a list of all users for admin review.
    Returns a partial if requested via HTMX.
    """
    try:
        users = User.query.with_entities(
            User.id,
            User.username,
            User.email,
            User.role,
            User.is_enabled,
            User.mfa_enabled,
            User.locked_until,
        ).all()
        roles = ["user", "admin"]
        log_info_message(f"Access - {current_user.username} - User List")

        template = (
            "admin/list_users_partial.html"
            if request.headers.get("HX-Request")
            else "admin/list_users_full.html"
        )
        return render_template(template, users=users, roles=roles, current_time=datetime.now(UTC))

    except Exception as e:
        log_exception_with_traceback("Failed to render user list", e)
        flash(_("Failed to load user list."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# View: Create a new user
# ---------------------------------------------------------------------
@bp.route("create/", methods=["GET", "POST"], strict_slashes=False)
@login_required
@admin_required
def create_user():
    """
    Admin view to create a new user.
    Renders full layout for normal requests, partial for HTMX.
    """
    form = CreateUserForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        role = form.role.data
        password = form.new_password.data

        if not password:
            flash(_("Password is required when creating a new user."), "danger")
            log_info_message(
                f"Admin '{current_user.username}' attempted to create user '{username}' without password."
            )
        elif User.query.filter_by(username=username).first():
            flash(_("Username already exists."), "danger")
            log_info_message(
                f"Admin '{current_user.username}' attempted to create duplicate username '{username}'."
            )
        elif User.query.filter_by(email=email).first():
            flash(_("Email already exists."), "danger")
            log_info_message(
                f"Admin '{current_user.username}' attempted to create duplicate email '{email}'."
            )
        else:
            try:
                user = User(
                    username=username,
                    email=email,
                    role=role,
                    password_hash=generate_password_hash(password),
                )
                db.session.add(user)
                db.session.commit()
                flash(
                    _("User '%(username)s' created successfully.") % {"username": username},
                    "success",
                )
                log_info_message(f"Admin '{current_user.username}' created new user '{username}'.")
                return redirect(url_for("users.list_users"))

            except Exception:
                db.session.rollback()
                flash(_("Failed to create user."), "danger")
                log_exception_with_traceback("Error during user creation.")

    template = (
        "admin/create_user_partial.html"
        if request.headers.get("HX-Request")
        else "admin/create_user_full.html"
    )
    return render_template(template, form=form)


# ---------------------------------------------------------------------
# View: Edit a specific user
# ---------------------------------------------------------------------
@bp.route("edit/<int:user_id>/", methods=["GET", "POST"], strict_slashes=False)
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash(_("User not found."), "danger")
        log_info_message(
            f"Admin '{current_user.username}' attempted to edit missing user ID={user_id}."
        )
        return redirect(url_for("users.list_users"))

    form = EditUserForm()

    if request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        log_info_message(
            f"Admin '{current_user.username}' opened edit form for user '{user.username}' (ID={user.id})."
        )

    if form.validate_on_submit():
        new_username = form.username.data.strip()
        new_email = form.email.data.strip()

        # Check for username conflict (but exclude current user)
        if User.query.filter(User.username == new_username, User.id != user.id).first():
            flash(_("Username already exists."), "danger")
            log_info_message(
                f"Admin '{current_user.username}' tried to change username to existing one '{new_username}'."
            )

        # Check for email conflict (exclude current user)
        elif User.query.filter(User.email == new_email, User.id != user.id).first():
            flash(_("Email already exists."), "danger")
            log_info_message(
                f"Admin '{current_user.username}' tried to change email to existing one '{new_email}'."
            )

        else:
            user.username = new_username
            user.email = new_email
            if form.new_password.data:
                user.password_hash = generate_password_hash(form.new_password.data.strip())

            try:
                db.session.commit()
                flash(_("User updated successfully."), "success")
                log_info_message(
                    f"Admin '{current_user.username}' updated user '{user.username}' (ID={user.id})."
                )
                return redirect(url_for("users.list_users"))
            except Exception as e:
                db.session.rollback()
                flash(_("An error occurred while updating the user."), "danger")
                log_exception_with_traceback("Failed to update user.", e)

    # Original — always rendered full layout
    return render_template("admin/edit_user.html", form=form, user=user)


# ---------------------------------------------------------------------
# View: Delete a specific user
# ---------------------------------------------------------------------
@bp.route("delete/<int:user_id>/", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def delete_user(user_id):
    """
    Delete a user and all associated data.
    """
    user = db.session.get(User, user_id)
    if not user:
        flash(_("User not found."), "danger")
        log_info_message(
            f"Admin '{current_user.username}' attempted to delete missing user ID={user_id}."
        )
        return redirect(url_for("users.list_users"))

    try:
        from app.models import (
            AppriseURL,
            EmailMessage,
            Message,
            UserMailSettings,
            Webhook,
            email_smtp_links,
            message_apprise_links,
            message_webhook_links,
        )

        log_info_message(
            f"Admin '{current_user.username}' began deleting user '{user.username}' (ID={user.id})."
        )

        db.session.execute(
            message_apprise_links.delete().where(
                message_apprise_links.c.message_id.in_(
                    db.session.query(Message.id).filter_by(user_id=user_id)
                )
            )
        )
        db.session.execute(
            message_webhook_links.delete().where(
                message_webhook_links.c.message_id.in_(
                    db.session.query(Message.id).filter_by(user_id=user_id)
                )
            )
        )
        db.session.execute(
            email_smtp_links.delete().where(
                email_smtp_links.c.email_id.in_(
                    db.session.query(EmailMessage.id).filter_by(user_id=user_id)
                )
            )
        )

        AppriseURL.query.filter_by(user_id=user_id).delete()
        Webhook.query.filter_by(user_id=user_id).delete()
        Message.query.filter_by(user_id=user_id).delete()
        for email in EmailMessage.query.filter_by(user_id=user_id).all():
            db.session.delete(email)
        UserMailSettings.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()

        flash(_("User deleted."), "success")
        log_info_message(
            f"Admin '{current_user.username}' deleted user '{user.username}' (ID={user.id})."
        )

    except Exception:
        db.session.rollback()
        flash(_("An error occurred while deleting the user."), "danger")
        log_exception_with_traceback("Failed to delete user and related data.")

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Toggle enabled status
# ---------------------------------------------------------------------
@bp.route("<int:user_id>/toggle-enabled", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def toggle_user_enabled(user_id):
    """
    Toggle a user's active/enabled status.
    """
    if user_id == current_user.id:
        flash(_("You cannot change your own enabled status."), "warning")
        log_info_message(f"Admin '{current_user.username}' attempted to disable self.")
        return redirect(url_for("users.list_users"))

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    try:
        user.is_enabled = not user.is_enabled
        db.session.commit()
        state = "enabled" if user.is_enabled else "disabled"

        try:
            send_email(
                to=user.email,
                subject=f"Your Grylli Account Was {state.capitalize()}",
                body=f"""Hello {user.username},

Your Grylli account has been {state} by an administrator.

If this was unexpected, please contact support.

- Grylli Team
""",
            )
            log_info_message(f"Users - {user.username} - {state.capitalize()} email sent")
        except Exception as e:
            log_exception_with_traceback(f"Users - {user.username} - Failed to send {state} email", e)

        flash(
            _("User '%(username)s' has been %(status)s.")
            % {"username": user.username, "status": _(state)},
            "success",
        )
        log_info_message(
            f"Admin '{current_user.username}' toggled user '{user.username}' to {state}."
        )
    except Exception:
        db.session.rollback()
        flash(_("An error occurred while updating the user."), "danger")
        log_exception_with_traceback("Failed to toggle user enabled status.")

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Reset MFA for a user
# ---------------------------------------------------------------------
@bp.route("reset-mfa/<int:user_id>/", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def reset_user_mfa(user_id):
    """
    Reset MFA for a specified user.
    """
    if user_id == current_user.id:
        flash(_("You cannot reset your own MFA."), "warning")
        log_info_message(f"Admin '{current_user.username}' attempted to reset own MFA.")
        return redirect(url_for("users.list_users"))

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    try:
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_recovery_codes = None
        db.session.commit()

        try:
            send_email(
                to=user.email,
                subject="Your MFA Was Reset by an Administrator",
                body=f"""Hello {user.username},

Your multi-factor authentication (MFA) was reset by an administrator.

If you did not request this, please contact support immediately.

- Grylli Team
""",
            )
            log_info_message(f"Users - {user.username} - MFA reset email notification sent")
        except Exception as e:
            log_exception_with_traceback(f"Users - {user.username} - Failed to send MFA reset email", e)

        flash(_("MFA disabled for user '%(username)s'.") % {"username": user.username}, "success")
        log_info_message(f"Admin '{current_user.username}' reset MFA for user '{user.username}'.")
    except Exception:
        db.session.rollback()
        flash(_("An error occurred while resetting MFA."), "danger")
        log_exception_with_traceback("Failed to reset user MFA.")

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Change Role
# ---------------------------------------------------------------------
@bp.route("<int:user_id>/change_role", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def change_role(user_id):
    """
    Change a user's role.
    """
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    new_role = request.form.get("role")

    if new_role not in ["user", "admin"]:
        flash(_("Invalid role"), "danger")
        return redirect(url_for("users.list_users"))

    try:
        user.role = new_role
        db.session.commit()

        try:
            send_email(
                to=user.email,
                subject="Your Grylli Role Was Changed",
                body=f"""Hello {user.username},

Your role in Grylli has been changed by an administrator.
Your new role is: {new_role}

If you did not expect this change, please contact support immediately.

- Grylli Team
""",
            )

            flash(_("Role updated for %(username)s.") % {"username": user.username}, "success")
            log_info_message(
                f"Admin '{current_user.username}' changed role of '{user.username}' to '{new_role}'."
            )
        except Exception as e:
            log_exception_with_traceback(f"Users - {user.username} - Failed to send role change email", e)
    except Exception:
        db.session.rollback()
        flash(_("An error occurred while updating the role."), "danger")
        log_exception_with_traceback("Failed to change user role.")

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Unlock User
# ---------------------------------------------------------------------
@bp.route("<int:user_id>/unlock", methods=["POST"], strict_slashes=False)
@admin_required
@login_required
def unlock_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if user is None:
            abort(404)

        user.locked_until = None
        db.session.commit()

        try:
            send_email(
                to=user.email,
                subject="Your Grylli Account Was Unlocked",
                body=f"""Hello {user.username},

Your account has been manually unlocked by an administrator.

If this was unexpected, please contact support.

- Grylli Team
""",
            )
            log_info_message(f"Users - {user.username} - Unlock email sent")
        except Exception as e:
            log_exception_with_traceback(f"Users - {user.username} - Failed to send unlock email", e)

        flash(_("User account unlocked."), "success")
        log_info_message(f"Admin '{current_user.username}' unlocked user '{user.username}'.")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Failed to unlock user account", e)
        flash(_("An error occurred while unlocking the account."), "danger")

    return redirect(url_for("users.list_users"))
