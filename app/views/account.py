"""
# ---------------------------------------------------------------------
# account.py
# app/views/account.py
# Blueprint for managing user account settings and translations info.
# ---------------------------------------------------------------------
"""

import io
import json
import traceback  # Add at the top if not already present

from flask import Blueprint, current_app, flash, redirect, render_template, send_file, url_for
from flask_babel import _
from flask_login import current_user, login_required, logout_user
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import GITHUB_URL
from app.forms.account_form import AccountForm
from app.models import (
    AppriseURL,
    EmailFileLink,
    EmailMessage,
    Message,
    Reminder,
    UserMailSettings,
    Webhook,
    db,
    email_smtp_links,
    message_apprise_links,
    message_webhook_links,
    reminder_apprise_links,
    reminder_email_links,
    reminder_smtp_links,
    reminder_webhook_links,
)
from app.services.mail import send_email
from app.utils.logging import log_error_message, log_info_message
from app.utils.serialization import model_to_dict

bp = Blueprint("account", __name__)


# ---------------------------------------------------------------------
# Route: Manage Account (view and update user account info)
# ---------------------------------------------------------------------
@bp.route("/account", methods=["GET", "POST"])
@login_required
def manage_account():
    """
    Route: Manage Account (view and update user account info)

    This route renders the `manage_account.html` template, displaying the user's current
    account information. The form is pre-populated with the current user's data. If the user
    submits the form, the route updates the user's account information in the database
    and redirects the user to the same page with a success message. If there is an error,
    the route redirects the user to the same page with an error message.

    The route requires the user to be logged in and will redirect an anonymous user to the
    login page.

    :param: None
    :return: render_template("account/manage_account.html", form=form)
    """
    form = AccountForm(obj=current_user)

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()

        if form.new_password.data:
            if not form.current_password.data:
                flash(_("Current password is required to change password."), "danger")
                return render_template("account/manage_account.html", form=form)

            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash(_("Current password is incorrect."), "danger")
                return render_template("account/manage_account.html", form=form)

            current_user.password_hash = generate_password_hash(form.new_password.data)
            log_info_message(f"User '{current_user.username}' changed their password.")

        # Update the fields
        current_user.username = username
        current_user.email = email

        try:
            db.session.commit()
            if username != current_user.username or email != current_user.email:
                log_info_message(
                    f"User '{current_user.username}' updated profile info: username='{username}', email='{email}'"
                )
            flash(_("Account updated successfully."), "success")
            log_info_message(f"User '{current_user.username}' updated their account.")
            return redirect(url_for("account.manage_account"))
        except Exception as e:
            db.session.rollback()
            log_error_message(f"Failed to update user {current_user.id}: {e}")
            flash(_("An error occurred while updating your account."), "danger")

    return render_template("account/manage_account.html", form=form)


# ---------------------------------------------------------------------
# Route: Translations Info Page
# ---------------------------------------------------------------------
@bp.route("/account/translations")
@login_required
def translations_info():
    """
    Route: Display information about Grylli translations
    """
    return render_template("account/translations.html", github_url=GITHUB_URL)


# ---------------------------------------------------------------------
# Route: Delete Account (POST only)
# ---------------------------------------------------------------------
@bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    """
    Route: Permanently delete the logged-in user's account.

    This will log the user out, delete the user from the database,
    and redirect to the home page with a success message.
    """
    username = current_user.username
    user_id = current_user.id

    try:
        # Prevent deletion if user is last admin
        if current_user.role == "admin":
            admin_count = User.query.filter_by(role="admin").count()
            if admin_count <= 1:
                flash(_("You cannot delete your account because you are the last admin."), "danger")
                return redirect(url_for("account.manage_account"))

        # Send the deletion email before deleting the user
        send_account_deleted_email(current_user)

        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        flash(_("Your account has been permanently deleted."), "success")
        log_info_message(f"User '{username}' (ID: {user_id}) deleted their account.")
    except Exception as e:
        db.session.rollback()
        log_error_message(f"Failed to delete account for user {user_id}: {e}")
        traceback.print_exc()  # ← This will help debug during dev
        flash(_("An error occurred while trying to delete your account."), "danger")

    return redirect(url_for("index.index"))


# ---------------------------------------------------------------------
# Email to user on account deletion
# ---------------------------------------------------------------------
def send_account_deleted_email(user):
    """
    Send an account deletion notification email to the user.

    This function sends an email to the user's registered email address when
    their account is deleted. The email notifies the user about the deletion,
    reminds them to remove any files from the uploads folder, and provides
    a contact option if the deletion was not initiated by them.

    :param user: User object representing the account being deleted.
    """
    subject = _("Your account has been deleted")
    body = _(
        "Hello {username},\n\nYour account on {site_name} has been deleted."
        "Remember to delete your files from the uploads folder."
        "If this was not you, please contact support immediately.\n\n{site_url}"
    ).format(
        username=user.username,
        site_name=current_app.config.get("SITE_NAME", "Grylli"),
        site_url=current_app.config.get("SITE_URL", "https://your.site"),
    )
    send_email(user.email, subject, body)


# ---------------------------------------------------------------------
# Export logged in user data to json
# ---------------------------------------------------------------------
@bp.route("/account/export", methods=["GET"])
@login_required
def export_account_data():
    """
    Export all user-owned data, including join tables,
    as decrypted JSON for user reference.
    """
    user_id = current_user.id

    # Use the helper for each model; specify which fields should be decrypted
    user_data = model_to_dict(
        current_user,
        decrypted_fields=["mfa_secret", "mfa_recovery_codes"],
        exclude_fields=["password_hash"],
    )
    reminders = [
        model_to_dict(reminder) for reminder in Reminder.query.filter_by(user_id=user_id).all()
    ]
    messages = [
        model_to_dict(message) for message in Message.query.filter_by(user_id=user_id).all()
    ]
    email_messages = [
        model_to_dict(email) for email in EmailMessage.query.filter_by(user_id=user_id).all()
    ]
    smtp_configs = [
        model_to_dict(smtp, decrypted_fields=["smtp_password"])
        for smtp in UserMailSettings.query.filter_by(user_id=user_id).all()
    ]
    apprise_urls = [
        model_to_dict(apprise, decrypted_fields=["url"])
        for apprise in AppriseURL.query.filter_by(user_id=user_id).all()
    ]
    webhooks = [
        model_to_dict(webhook, decrypted_fields=["endpoint"])
        for webhook in Webhook.query.filter_by(user_id=user_id).all()
    ]
    email_file_links = [
        {
            "message_id": link.message_id,
            "file_path": link.file_path,
        }
        for link in EmailFileLink.query.join(
            EmailMessage, EmailMessage.id == EmailFileLink.message_id
        )
        .filter(EmailMessage.user_id == user_id)
        .all()
    ]

    # Helper lists of IDs for join filtering
    reminder_ids = [reminder["id"] for reminder in reminders]
    message_ids = [message["id"] for message in messages]
    email_ids = [email["id"] for email in email_messages]

    # Join tables: only rows related to this user's data
    reminder_apprise = [
        dict(row)
        for row in db.session.execute(
            select(reminder_apprise_links).where(
                reminder_apprise_links.c.reminder_id.in_(reminder_ids)
            )
        )
    ]
    reminder_webhook = [
        dict(row)
        for row in db.session.execute(
            select(reminder_webhook_links).where(
                reminder_webhook_links.c.reminder_id.in_(reminder_ids)
            )
        )
    ]
    reminder_smtp = [
        dict(row)
        for row in db.session.execute(
            select(reminder_smtp_links).where(reminder_smtp_links.c.reminder_id.in_(reminder_ids))
        )
    ]
    reminder_email = [
        dict(row)
        for row in db.session.execute(
            select(reminder_email_links).where(reminder_email_links.c.reminder_id.in_(reminder_ids))
        )
    ]
    message_apprise = [
        dict(row)
        for row in db.session.execute(
            select(message_apprise_links).where(message_apprise_links.c.message_id.in_(message_ids))
        )
    ]
    message_webhook = [
        dict(row)
        for row in db.session.execute(
            select(message_webhook_links).where(message_webhook_links.c.message_id.in_(message_ids))
        )
    ]
    email_smtp = [
        dict(row)
        for row in db.session.execute(
            select(email_smtp_links).where(email_smtp_links.c.email_id.in_(email_ids))
        )
    ]

    # Compose the full export structure
    export = {
        "user": user_data,
        "reminders": reminders,
        "messages": messages,
        "email_messages": email_messages,
        "smtp_configs": smtp_configs,
        "apprise_urls": apprise_urls,
        "webhooks": webhooks,
        "email_file_links": email_file_links,
        "join_tables": {
            "reminder_apprise_links": reminder_apprise,
            "reminder_webhook_links": reminder_webhook,
            "reminder_smtp_links": reminder_smtp,
            "reminder_email_links": reminder_email,
            "message_apprise_links": message_apprise,
            "message_webhook_links": message_webhook,
            "email_smtp_links": email_smtp,
        },
    }

    buffer = io.BytesIO(json.dumps(export, indent=2, default=str).encode("utf-8"))
    filename = f"{current_user.username}_grylli_export.json"

    log_info_message(
        f"User '{current_user.username}' (ID: {current_user.id}) exported their account data."
    )

    return send_file(
        buffer, as_attachment=True, download_name=filename, mimetype="application/json"
    )
