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

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_babel import _, get_locale
from flask_login import current_user, login_required, logout_user
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import GITHUB_URL
from app.forms.account_form import AccountForm
from app.forms.security_questions_form import SecurityQuestionsForm
from app.models import (
    AppriseURL,
    EmailFileLink,
    EmailMessage,
    Message,
    Reminder,
    User,
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
from app.services.security_questions import save_security_questions
from app.utils.logging import (
    log_debug_message,
    log_error_message,
    log_exception_with_traceback,
    log_info_message,
    log_user_action,
)
from app.utils.serialization import model_to_dict

bp = Blueprint("account", __name__)


# ---------------------------------------------------------------------
# Route: Manage Account (HTMX and full render support)
# ---------------------------------------------------------------------
@bp.route("account", methods=["GET", "POST"], strict_slashes=False)
@login_required
def manage_account():
    """
    Route: Manage Account (view and update user account info).
    Supports full and partial HTMX-based rendering.

    - Renders 'account/partials/manage_account.html' if HX-Request.
    - Renders 'account/manage_account_full.html' otherwise.
    """
    log_info_message(f"Access - {current_user.username} - Account Management")

    form = AccountForm(obj=current_user)

    if form.validate_on_submit():
        new_username = form.username.data.strip()
        new_email = form.email.data.strip()

        # Check password update request
        if form.new_password.data:
            if not form.current_password.data:
                flash(_("Current password is required to change password."), "danger")
                return render_template("account/partials/manage_account.html", form=form)

            if not current_user.check_password(form.current_password.data):
                flash(_("Current password is incorrect."), "danger")
                return render_template("account/partials/manage_account.html", form=form)

            current_user.password_hash = generate_password_hash(form.new_password.data)
            log_info_message(f"User '{current_user.username}' changed their password.")

        updated_fields = []
        if new_username != current_user.username:
            updated_fields.append(f"username='{new_username}'")
            current_user.username = new_username
        if new_email != current_user.email:
            updated_fields.append(f"email='{new_email}'")
            current_user.email = new_email

        try:
            db.session.commit()
            if updated_fields:
                log_user_action(
                    "Account",
                    "Edit",
                    current_user,  # required positional `obj`
                    username=current_user.username,
                    extra=f"Updated fields: {', '.join(updated_fields)}",
                )

                flash(_("Account updated successfully."), "success")
            else:
                log_debug_message(f"No changes submitted for user '{current_user.username}'")
                flash(_("No changes made."), "info")
            return redirect(url_for("account.manage_account"))

        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback(f"Failed to update account for user {current_user.id}", e)
            flash(_("An error occurred while updating your account."), "danger")

    template = (
        "account/manage_account_partial.html"
        if request.headers.get("HX-Request") == "true"
        else "account/manage_account_full.html"
    )

    is_last_admin = (
        current_user.role == "admin"
        and User.query.filter_by(role="admin", is_enabled=True).count() == 1
    )

    return render_template(template, form=form, is_last_admin=is_last_admin)

# ---------------------------------------------------------------------
# Route: Translations Info Page
# ---------------------------------------------------------------------
@bp.route("account/translations", strict_slashes=False)
@login_required
def translations_info():
    try:
        log_info_message(f"Access - {current_user.username} - Translations Info")

        context = {
            "github_url": GITHUB_URL,
            "lang_code": str(get_locale()),
        }

        if "HX-Request" in request.headers:
            return render_template("account/translations_partial.html", **context)
        else:
            return render_template("account/translations_full.html", **context)

    except Exception as e:
        tb = traceback.format_exc()
        print("=== TRANSLATION RENDER ERROR ===")
        print(tb)
        log_exception_with_traceback("Error rendering Translations Info page", e)
        flash(_("An error occurred while loading translation info."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Route: Delete Account (POST only)
# ---------------------------------------------------------------------
@bp.route("account/delete", methods=["POST"], strict_slashes=False)
@login_required
def delete_account():
    """
    Route: Permanently delete the logged-in user's account.

    This will log the user out, delete the user from the database,
    and redirect to the home page with a success message.
    """

    log_info_message(f"Access - {current_user.username} - Account Delete")

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
        log_user_action(
            "Acount", "Delete", details=f"User '{username}' (ID: {user_id}) deleted their account"
        )
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback(f"Failed to delete account for user {user_id}", e)
        flash(_("An error occurred while trying to delete your account."), "danger")

    return redirect(url_for("home.index"))


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
        site_url=current_app.config.get("SITE_URL", "http://osu.grylli:5069/grylli/"),
    )
    send_email(user.email, subject, body)


# ---------------------------------------------------------------------
# Export logged in user data to json
# ---------------------------------------------------------------------
@bp.route("account/export", methods=["GET"], strict_slashes=False)
@login_required
def export_account_data():
    """
    Export all user-owned data, including join tables,
    as decrypted JSON for user reference.
    """

    log_info_message(f"Access - {current_user.username} - Account Export")

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
        dict(row._mapping)
        for row in db.session.execute(
            select(reminder_apprise_links).where(
                reminder_apprise_links.c.reminder_id.in_(reminder_ids)
            )
        )
    ]
    reminder_webhook = [
        dict(row._mapping)
        for row in db.session.execute(
            select(reminder_webhook_links).where(
                reminder_webhook_links.c.reminder_id.in_(reminder_ids)
            )
        )
    ]
    reminder_smtp = [
        dict(row._mapping)
        for row in db.session.execute(
            select(reminder_smtp_links).where(reminder_smtp_links.c.reminder_id.in_(reminder_ids))
        )
    ]
    reminder_email = [
        dict(row._mapping)
        for row in db.session.execute(
            select(reminder_email_links).where(reminder_email_links.c.reminder_id.in_(reminder_ids))
        )
    ]
    message_apprise = [
        dict(row._mapping)
        for row in db.session.execute(
            select(message_apprise_links).where(message_apprise_links.c.message_id.in_(message_ids))
        )
    ]
    message_webhook = [
        dict(row._mapping)
        for row in db.session.execute(
            select(message_webhook_links).where(message_webhook_links.c.message_id.in_(message_ids))
        )
    ]
    email_smtp = [
        dict(row._mapping)
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

    log_user_action("Account", "View", "Exported user account data")

    return send_file(
        buffer, as_attachment=True, download_name=filename, mimetype="application/json"
    )


# ---------------------------------------------------------------------
# Route: Set or update security questions
# ---------------------------------------------------------------------
@bp.route("account/set_security_questions", methods=["GET", "POST"], strict_slashes=False)
@login_required
def set_security_questions():
    """
    Render and process the security questions form. Allows both initial setup
    and subsequent updates to existing questions. Responds with either full or
    partial template depending on HTMX request or bootstrap flag.
    """
    from flask import flash, redirect, render_template, request, url_for, session
    from flask_login import current_user

    from app.extensions import db
    from app.forms.security_questions_form import SecurityQuestionsForm
    from app.services.security_questions import hash_answer, save_security_questions
    from app.utils.logging import log_exception_with_traceback, log_info_message

    log_info_message(f"Access - {current_user.username} - Account Security Questions")

    form = SecurityQuestionsForm()
    existing = current_user.security_questions

    try:
        if request.method == "GET" and existing:
            form.question_1.data = existing.question_1
            form.question_2.data = existing.question_2
            form.question_3.data = existing.question_3

        if form.validate_on_submit():
            q1 = form.question_1.data
            q2 = form.question_2.data
            q3 = form.question_3.data

            if len({q1, q2, q3}) < 3:
                flash(_("Each security question must be different."), "danger")
                return render_template(
                    "account/bootstrap_security_questions.html"
                    if session.get("bootstrap_complete")
                    else (
                        "account/set_security_questions_partial.html"
                        if request.headers.get("HX-Request") == "true"
                        else "account/set_security_questions_full.html"
                    ),
                    form=form
                )

            if existing:
                existing.question_1 = form.question_1.data
                existing.answer_1_hash = hash_answer(form.answer_1.data)
                existing.question_2 = form.question_2.data
                existing.answer_2_hash = hash_answer(form.answer_2.data)
                existing.question_3 = form.question_3.data
                existing.answer_3_hash = hash_answer(form.answer_3.data)
            else:
                save_security_questions(current_user, form)

            db.session.commit()
            session.pop("bootstrap_complete", None)
            flash(_("Security questions saved."), "success")
            return redirect(url_for("home.index"))

        # Template selection
        if session.get("bootstrap_complete"):
            template = "account/bootstrap_security_questions.html"
        elif request.headers.get("HX-Request") == "true":
            template = "account/set_security_questions_partial.html"
        else:
            template = "account/set_security_questions_full.html"

        return render_template(template, form=form)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Failed to save or render security questions", e)
        flash(_("An error occurred while saving your security questions."), "danger")
        return redirect(url_for("home.index"))
