"""
# ---------------------------------------------------------------------
# email.py
# app/views/email.py
# Blueprint for secure email message creation, viewing, and testing.
# ---------------------------------------------------------------------
"""

import os
import subprocess
from datetime import datetime

from cryptography.fernet import InvalidToken
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.forms.email_form import (
    AssignSmtpForm,
    AttachFilesForm,
    EmailMessageForm,
    UserMailSettingsForm,
)
from app.forms.message_form import ScheduleForm
from app.models import EmailFileLink, EmailMessage, UserMailSettings, db
from app.services.encryption import decrypt, encrypt
from app.utils.duration import load_minutes_into_form_parts, total_minutes_from_form_parts
from app.utils.file_utils import list_available_files
from app.utils.logging import log_info_message

bp = Blueprint("email", __name__)


# ---------------------------------------------------------------------
# List all secure email messages
# ---------------------------------------------------------------------
@bp.route("/")
@login_required
def index():
    """
    Show a list of all secure email messages that the user has created.

    Only secure email messages that the user has created will be shown.
    """
    emails = EmailMessage.query.filter_by(user_id=current_user.id).all()
    return render_template("email/list_emails.html", emails=emails)


# ---------------------------------------------------------------------
# Create or edit a secure email message
# ---------------------------------------------------------------------
@bp.route("/create", methods=["GET", "POST"])
@bp.route("/<int:message_id>/edit", methods=["GET", "POST"])
@login_required
def edit_message(message_id=None):
    """
    Create or edit a secure email message.

    If message_id is provided, the secure email message with the given ID
    will be retrieved and edited. Otherwise, a new secure email message will
    be created.

    The user will be presented with a form to enter the details of the
    secure email message. The form fields are validated and the message is
    saved to the database when the form is submitted.

    If the message is successfully saved, a success message is flashed and
    the user is redirected to the secure email message index page.

    :param message_id: The ID of the secure email message to edit, or None
        if a new secure email message should be created.
    :return: A rendered template displaying the secure email message edit
        form, or a redirect response on successful message save.
    """
    if message_id:
        message = EmailMessage.query.filter_by(
            id=message_id, user_id=current_user.id
        ).first_or_404()
        form = EmailMessageForm(obj=message)
    else:
        message = EmailMessage(user_id=current_user.id)
        form = EmailMessageForm()

    if form.validate_on_submit():
        form.populate_obj(message)
        db.session.add(message)
        db.session.commit()
        flash(_("Message saved."), "success")
        log_info_message(f"User '{current_user.username}' saved email message ID={message.id}.")
        return redirect(url_for("email.index"))

    return render_template("email/edit_message.html", form=form, message=message)


# ---------------------------------------------------------------------
# Delete a secure email message
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    """
    Handle the deletion of a secure email message for the current user.

    Retrieves a message identified by the message_id parameter,
    and deletes it from the database if it belongs to the current user.
    On successful deletion, a success message is flashed, and the user
    is redirected to the secure email message index page.

    Args:
        message_id (int): The ID of the message to be deleted.

    Returns:
        Response: A redirect response to the secure email message index page.
    """
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    db.session.delete(message)
    db.session.commit()
    flash(_("Message deleted."), "success")
    log_info_message(f"User '{current_user.username}' deleted email message ID={message_id}.")
    return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Attach files to a message
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/files", methods=["GET", "POST"])
@login_required
def attach_files(message_id):
    """
    View to attach files to a message.

    :param int message_id: ID of the message to attach files to.

    Only files in the uploads directory will be available to be attached.
    """
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    existing = {f.file_path for f in message.files}

    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "uploads"))
    available_files = list_available_files(upload_dir)
    existing = {f.file_path for f in message.files}

    if request.method == "POST":
        selected = request.form.getlist("file_paths")
        message.files.clear()
        for f in selected:
            message.files.append(EmailFileLink(file_path=f))
        db.session.commit()
        log_info_message(
            f"User '{current_user.username}' updated attachments for email ID={message_id}."
        )
        flash(_("Attached files updated."), "success")
        return redirect(url_for("email.index"))

    # When rendering, pass both name and size for each file
    return render_template(
        "email/attach_files.html",
        message=message,
        available_files=available_files,  # List of {'name': ..., 'size': ...}
        existing_files=existing,
    )


# ---------------------------------------------------------------------
# View message + SMTP config + attachments
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/view", methods=["GET"])
@login_required
def view_config(message_id):
    """
    View the configuration of a message.

    Displays the message details, SMTP configuration,
    and any attachments associated with the message.

    :param int message_id: ID of the message to view.
    """
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()
    log_info_message(f"User '{current_user.username}' viewed config for email ID={message_id}.")
    return render_template("email/view_config.html", message=message, smtp=smtp)


# ---------------------------------------------------------------------
# Send test email (via Apprise CLI)
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/send-test", methods=["POST"])
@login_required
def send_test(message_id):
    """
    Sends a test email for the specified message using Apprise.

    Fetches the assigned SMTP config (via join table), builds the Apprise URL,
    and sends the message with any attachments to the logged-in user.
    """
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    smtp = message.smtp_configs[0] if message.smtp_configs else None

    if not smtp or not smtp.enabled:
        flash(_("SMTP configuration not assigned or is disabled."), "danger")
        return redirect(url_for("email.view_config", message_id=message.id))

    # Password already decrypted via property
    decrypted_password = smtp.smtp_password

    # Build the Apprise mailto URL
    apprise_url = (
        f"mailtos://{current_user.email}"
        f"?smtp={smtp.smtp_host}"
        f"&user={smtp.smtp_username}"
        f"&pass={decrypted_password}"
        f"&secure=starttls"
    )

    # Construct Apprise command
    cmd = [
        "apprise",
        "--title",
        message.subject,
        "--body",
        message.body,
    ]

    for f in message.files:
        cmd += ["--attach", os.path.join("uploads", f.file_path)]

    cmd.append(apprise_url)

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        log_info_message(
            f"User '{current_user.username}' sent test email for message ID={message_id}."
        )
        flash(_("Test email sent successfully."), "success")
    except subprocess.CalledProcessError as e:
        flash(f"Email failed: {e.stderr or e.stdout or 'Unknown error'}", "danger")
        log_info_message(
            f"User '{current_user.username}' failed to send test email ID={message_id}: {e}"
        )
    return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Email Schedule (Check-in & Grace Period)
# ---------------------------------------------------------------------
@bp.route("/schedule/<int:message_id>", methods=["GET", "POST"])
@login_required
def schedule(message_id):
    """
    Handles scheduling of a secure email.

    Allows the user to edit the scheduling of a secure email, including
    the check-in interval and grace period. The user must be the owner of
    the secure email to be able to edit it.

    :param message_id: The ID of the secure email message to be edited.
    :returns: Redirects to the list of secure email messages with a success
        or error flash message.
    """
    message = EmailMessage.query.get_or_404(message_id)

    if message.user_id != current_user.id:
        flash(_("Access denied."), "danger")
        return redirect(url_for("email.index"))

    form = ScheduleForm()

    # Pre-fill form on GET
    if request.method == "GET":
        if message.checkin_interval_minutes:
            load_minutes_into_form_parts(form, "checkin", message.checkin_interval_minutes)
        if message.grace_period_minutes:
            load_minutes_into_form_parts(form, "grace", message.grace_period_minutes)

    if form.validate_on_submit():
        message.checkin_interval_minutes = total_minutes_from_form_parts(form, "checkin")
        message.grace_period_minutes = total_minutes_from_form_parts(form, "grace")
        db.session.commit()
        log_info_message(
            f"User '{current_user.username}' updated schedule for email ID={message_id}."
        )
        flash(_("Schedule updated successfully."), "success")
        return redirect(url_for("email.index"))

    return render_template("email/schedule_email.html", form=form, message=message)


# ---------------------------------------------------------------------
# Email SMTP Configuration Assignment
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/smtp", methods=["GET", "POST"])
@login_required
def assign_smtp(message_id):
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    smtp_options = UserMailSettings.query.filter_by(user_id=current_user.id).all()
    form = AssignSmtpForm()

    if request.method == "POST" and form.validate_on_submit():
        selected_id = request.form.get("smtp_config")
        if selected_id:
            selected = UserMailSettings.query.filter_by(
                id=selected_id, user_id=current_user.id
            ).first()
            if selected:
                message.smtp_configs = [selected]
                db.session.commit()
                log_info_message(
                    f"User '{current_user.username}' assigned SMTP config ID={selected_id} to email ID={message_id}."
                )
                flash(_("SMTP configuration assigned."), "success")
                return redirect(url_for("email.index"))
        else:
            # If no smtp_config is selected, unassign
            message.smtp_configs = []
            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' unassigned SMTP config from email ID={message_id}."
            )
            flash(_("SMTP configuration removed."), "info")
            return redirect(url_for("email.index"))

    return render_template(
        "email/assign_smtp.html", message=message, smtp_options=smtp_options, form=form
    )


# ---------------------------------------------------------------------
# Email Status
# ---------------------------------------------------------------------
@bp.route("/status", methods=["GET"])
@login_required
def email_status():
    """
    API endpoint to return the list of emails and their current enabled status
    for the logged-in user. Used for UI polling to refresh enabled/disabled states.
    """
    emails = EmailMessage.query.filter_by(user_id=current_user.id).all()

    email_status_list = [{"id": email.id, "is_enabled": email.is_enabled} for email in emails]

    return jsonify(email_status_list)
