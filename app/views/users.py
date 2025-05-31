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
    users = User.query.with_entities(
        User.id, User.username, User.email, User.role, User.is_enabled
    ).all()
    return render_template("admin/list_users.html", users=users)


# ---------------------------------------------------------------------
# View: Edit a specific user
# ---------------------------------------------------------------------
@bp.route("/edit/<int:user_id>/", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash(_("User not found."), "danger")
        return redirect(url_for("users.list_users"))

    form = EditUserForm()
    if request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role

    if form.validate_on_submit():
        user.username = form.username.data.strip()
        user.email = form.email.data.strip()
        user.role = form.role.data.strip()

        if form.new_password.data:
            user.password_hash = generate_password_hash(form.new_password.data.strip())

        try:
            db.session.commit()
            flash(_("User updated successfully."), "success")
            log_info_message(
                "Admin '%(admin)s' updated user '%(user)s'."
                % {"admin": current_user.username, "user": user.username}
            )
            return redirect(url_for("users.list_users"))
        except Exception as e:
            db.session.rollback()
            flash(_("An error occurred while updating the user."), "danger")
            log_error_message(
                "Failed to update user %(id)s: %(error)s" % {"id": user_id, "error": e}
            )

    return render_template("admin/edit_user.html", form=form, user_id=user_id)

# ---------------------------------------------------------------------
# View: Delete a specific user
# ---------------------------------------------------------------------
@bp.route("/delete/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash(_("User not found."), "danger")
        return redirect(url_for("users.list_users"))

    try:
        from app.models import (
            AppriseURL,
            Message,
            EmailMessage,
            UserMailSettings,
            Webhook,
            email_smtp_links,
            message_apprise_links,
            message_webhook_links,
        )

        # Delete join table rows for this user's messages and emails
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

        # Delete related objects by user_id
        AppriseURL.query.filter_by(user_id=user_id).delete()
        Webhook.query.filter_by(user_id=user_id).delete()
        Message.query.filter_by(user_id=user_id).delete()

        # Delete each EmailMessage via ORM to trigger cascade on EmailFileLink
        for email in EmailMessage.query.filter_by(user_id=user_id).all():
            db.session.delete(email)

        # Delete user's SMTP configs
        UserMailSettings.query.filter_by(user_id=user_id).delete()

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        flash(_("User deleted."), "success")
        log_info_message(
            "Admin '%(admin)s' deleted user '%(user)s'."
            % {"admin": current_user.username, "user": user.username}
        )
    except Exception as e:
        db.session.rollback()
        flash(_("An error occurred while deleting the user."), "danger")
        log_error_message("Failed to delete user %(id)s: %(error)s" % {"id": user_id, "error": e})

    return redirect(url_for("users.list_users"))

# ---------------------------------------------------------------------
# View: Create a new user
# ---------------------------------------------------------------------
@bp.route("/create/", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    form = EditUserForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        role = form.role.data
        password = form.new_password.data

        if not password:
            flash(_("Password is required when creating a new user."), "danger")
            return render_template("admin/create_user.html", form=form)

        if User.query.filter_by(username=username).first():
            flash(_("Username already exists."), "danger")
            return render_template("admin/create_user.html", form=form)

        if User.query.filter_by(email=email).first():
            flash(_("Email already exists."), "danger")
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
            return redirect(url_for("users.list_users"))

        except Exception as e:
            db.session.rollback()
            log_error_message("Error creating user: " + str(e))
            flash(_("Failed to create user."), "danger")

    return render_template("admin/create_user.html", form=form)


# ---------------------------------------------------------------------
# View: Toggle is_enabled for a user
# ---------------------------------------------------------------------
@bp.route("/<int:user_id>/toggle-enabled", methods=["POST"])
@login_required
@admin_required
def toggle_user_enabled(user_id):
    if user_id == current_user.id:
        flash(_("You cannot change your own enabled status."), "warning")
        return redirect(url_for("users.list_users"))

    user = User.query.get_or_404(user_id)

    try:
        user.is_enabled = not user.is_enabled
        db.session.commit()
        flash(
            _("User '%(username)s' has been %(status)s.")
            % {
                "username": user.username,
                "status": _("enabled") if user.is_enabled else _("disabled"),
            },
            "success",
        )
    except Exception as e:
        db.session.rollback()
        log_error_message("Failed to toggle user %(id)s: %(error)s" % {"id": user_id, "error": e})
        flash(_("An error occurred while updating the user."), "danger")

    return redirect(url_for("users.list_users"))
