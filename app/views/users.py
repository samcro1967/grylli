"""
# ---------------------------------------------------------------------
# users.py
# app/views/users.py
# Admin user management views for Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from app.forms.create_user_form import CreateUserForm
from app.forms.edit_user_form import EditUserForm
from app.models import User, db
from app.utils.logging import log_error_message, log_info_message
from app.views.auth import admin_required

bp = Blueprint("users", __name__)


# ---------------------------------------------------------------------
# View: List all users
# ---------------------------------------------------------------------
@bp.route("/")
@login_required
@admin_required
def list_users():
    """
    Display a list of all users.

    This view is accessible only to admin users and lists users with their
    basic information including ID, username, email, role, enabled status,
    and MFA status. The user list is rendered on the 'admin/list_users.html'
    template.

    Logs the action of viewing the user list by the current admin.
    """

    users = User.query.with_entities(
        User.id, User.username, User.email, User.role, User.is_enabled, User.mfa_enabled
    ).all()
    roles = ["user", "admin"]  # or however your app defines possible roles
    log_info_message(f"Admin '{current_user.username}' viewed user list.")
    return render_template("admin/list_users.html", users=users, roles=roles)


# ---------------------------------------------------------------------
# View: Edit a specific user
# ---------------------------------------------------------------------
@bp.route("/edit/<int:user_id>/", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    """
    Edit an existing user's details.

    This view is accessible only to admin users and allows the modification
    of a user's username, email, and password. If the user is not found,
    a flash message is displayed, and the admin is redirected to the user list.

    On a GET request, pre-fills the form with the current user details.
    On form submission, updates the user information if the form validates
    successfully. Commits changes to the database, flashes a success message,
    and logs the update action. If an error occurs during the update, a
    rollback is performed, an error message is flashed, and the error is logged.

    :param user_id: The ID of the user to be edited.
    :return: Redirects to the user list on successful update or renders the
             edit user form with the current user data.
    """

    user = User.query.get(user_id)
    if not user:
        flash(_("User not found."), "danger")
        log_error_message(
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
        user.username = form.username.data.strip()
        user.email = form.email.data.strip()

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
            log_error_message(f"Failed to update user ID={user_id}: {e}")

    return render_template("admin/edit_user.html", form=form, user_id=user_id)


# ---------------------------------------------------------------------
# View: Delete a specific user
# ---------------------------------------------------------------------
@bp.route("/delete/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """
    Delete a specific user and all associated data.

    This view is accessible only to admin users and handles the deletion
    of a user identified by the user_id parameter. It removes the user and
    all related data from the database, including messages, email links,
    and webhooks. If the user is not found, a flash message is displayed,
    and the admin is redirected to the user list.

    Logs the deletion process, and if an error occurs, a rollback is performed,
    an error message is flashed, and the error is logged.

    Args:
        user_id (int): The ID of the user to be deleted.

    Returns:
        Response: A redirect response to the user list page.
    """

    user = User.query.get(user_id)
    if not user:
        flash(_("User not found."), "danger")
        log_error_message(
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
            f"Admin '{current_user.username}' began deletion process for user '{user.username}' (ID={user.id})."
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

    except Exception as e:
        db.session.rollback()
        flash(_("An error occurred while deleting the user."), "danger")
        log_error_message(f"Failed to delete user ID={user_id}: {e}")

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Create a new user
# ---------------------------------------------------------------------
@bp.route("/create/", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    """
    Create a new user.

    This view is accessible only to admin users and allows the creation
    of a new user with a specified username, email, and role. If the
    form is invalid, the user is redirected back to the form with the
    validation errors displayed. If the user is created successfully,
    a success message is displayed and the user is redirected to the
    user list.

    :return: Redirects to the user list on successful creation or renders
             the create user form with validation errors on failure.
    """
    form = CreateUserForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        role = form.role.data
        password = form.new_password.data

        if not password:
            flash(_("Password is required when creating a new user."), "danger")
            log_error_message(
                f"Admin '{current_user.username}' attempted to create user '{username}' without a password."
            )
            return render_template("admin/create_user.html", form=form)

        if User.query.filter_by(username=username).first():
            flash(_("Username already exists."), "danger")
            log_error_message(
                f"Admin '{current_user.username}' attempted to create duplicate username '{username}'."
            )
            return render_template("admin/create_user.html", form=form)

        if User.query.filter_by(email=email).first():
            flash(_("Email already exists."), "danger")
            log_error_message(
                f"Admin '{current_user.username}' attempted to create duplicate email '{email}'."
            )
            return render_template("admin/create_user.html", form=form)

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
                _("User '%(username)s' created successfully.") % {"username": username}, "success"
            )
            log_info_message(f"Admin '{current_user.username}' created new user '{username}'.")
            return redirect(url_for("users.list_users"))

        except Exception as e:
            db.session.rollback()
            log_error_message(
                f"Admin '{current_user.username}' failed to create user '{username}': {e}"
            )
            flash(_("Failed to create user."), "danger")

    return render_template("admin/create_user.html", form=form)


# ---------------------------------------------------------------------
# View: Toggle is_enabled for a user
# ---------------------------------------------------------------------
@bp.route("/<int:user_id>/toggle-enabled", methods=["POST"])
@login_required
@admin_required
def toggle_user_enabled(user_id):
    """
    Toggle the enabled status of a specified user.

    This view is accessible only to admin users. It toggles the 'is_enabled'
    status of a user identified by 'user_id'. If the toggled user is the
    current admin, a warning is flashed, and the action is not performed.
    On successful toggle, a success message is flashed and the action is
    logged. If an error occurs, a rollback is performed, and an error
    message is flashed and logged.

    :param user_id: The ID of the user whose enabled status is to be toggled.
    :returns: A redirect response to the user list page.
    """

    if user_id == current_user.id:
        flash(_("You cannot change your own enabled status."), "warning")
        log_error_message(
            f"Admin '{current_user.username}' attempted to change their own enabled status."
        )
        return redirect(url_for("users.list_users"))

    user = User.query.get_or_404(user_id)

    try:
        user.is_enabled = not user.is_enabled
        db.session.commit()
        status_text = "enabled" if user.is_enabled else "disabled"
        flash(
            _("User '%(username)s' has been %(status)s.")
            % {"username": user.username, "status": _(status_text)},
            "success",
        )
        log_info_message(
            f"Admin '{current_user.username}' toggled user '{user.username}' to {status_text}."
        )
    except Exception as e:
        db.session.rollback()
        flash(_("An error occurred while updating the user."), "danger")
        log_error_message(
            f"Admin '{current_user.username}' failed to toggle user ID={user_id}: {e}"
        )

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Reset/Disable MFA for a user (admin only)
# ---------------------------------------------------------------------
@bp.route("/reset-mfa/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def reset_user_mfa(user_id):
    """
    Reset the Multi-Factor Authentication (MFA) for a specified user.

    This function is accessible only to admin users and allows them to
    reset the MFA settings for any user except themselves. It will
    disable MFA, clear the MFA secret, and remove any recovery codes
    for the specified user. The operation is logged, and appropriate
    success or error messages are flashed to the admin.

    :param user_id: The ID of the user whose MFA is to be reset.
    :returns: A redirect response to the user list page.
    """

    if user_id == current_user.id:
        flash(_("You cannot reset your own MFA."), "warning")
        log_error_message(f"Admin '{current_user.username}' attempted to reset their own MFA.")
        return redirect(url_for("users.list_users"))

    user = User.query.get_or_404(user_id)

    try:
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_recovery_codes = None
        db.session.commit()
        flash(
            _("MFA disabled for user '%(username)s'.") % {"username": user.username},
            "success",
        )
        log_info_message(f"Admin '{current_user.username}' reset MFA for user '{user.username}'.")
    except Exception as e:
        db.session.rollback()
        flash(_("An error occurred while resetting MFA."), "danger")
        log_error_message(
            f"Admin '{current_user.username}' failed to reset MFA for user ID={user_id}: {e}"
        )

    return redirect(url_for("users.list_users"))


# ---------------------------------------------------------------------
# View: Change Role
# ---------------------------------------------------------------------
@bp.route("/<int:user_id>/change_role", methods=["POST"])
@login_required
@admin_required  # If you have an admin_required decorator
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    # Validate new_role as needed!
    if new_role not in ["user", "admin"]:
        flash("Invalid role", "danger")
        return redirect(url_for("users.list_users"))
    user.role = new_role
    db.session.commit()
    flash(f"Role updated for {user.username}.", "success")
    return redirect(url_for("users.list_users"))
