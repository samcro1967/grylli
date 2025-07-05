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
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("email", __name__)


# ---------------------------------------------------------------------
# List all secure email messages
# ---------------------------------------------------------------------
@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
def index():
    """
    Display a list of secure email messages for the current user.
    Renders a full layout for normal requests, partial for HTMX.
    """
    try:
        emails = (
            db.session.query(EmailMessage)
            .filter_by(user_id=current_user.id)
            .order_by(EmailMessage.created_at.desc())
            .all()
        )
        log_info_message(f"User '{current_user.username}' viewed their email message list.")

        template = (
            "email/list_emails_partial.html"
            if request.headers.get("HX-Request")
            else "email/list_emails_full.html"
        )
        return render_template(template, emails=emails)

    except Exception as e:
        log_exception_with_traceback("Failed to load email message list", e)
        flash(_("Failed to load email messages."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Create or edit a secure email message
# ---------------------------------------------------------------------
@bp.route("create", methods=["GET", "POST"], strict_slashes=False)
@bp.route("<int:email_id>/edit", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_email(email_id=None):
    """
    Create or edit a secure email message.
    """
    try:
        if email_id:
            email = EmailMessage.query.filter_by(
                id=email_id, user_id=current_user.id
            ).first_or_404()
            form = EmailMessageForm(obj=email)
        else:
            email = EmailMessage(user_id=current_user.id)
            form = EmailMessageForm()

        if form.validate_on_submit():
            form.populate_obj(email)
            db.session.add(email)
            db.session.commit()
            flash(_("Message saved."), "success")
            log_info_message(f"User '{current_user.username}' saved email message ID={email.id}.")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "emailListChanged"
                return response

            return redirect(url_for("email.index"))

        template = (
            "email/edit_email_partial.html"
            if request.headers.get("HX-Request")
            else "email/edit_email_full.html"
        )
        return render_template(template, form=form, message=email)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("edit_email failed", e)
        flash(_("An error occurred while saving the message."), "danger")
        return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Delete a secure email message
# ---------------------------------------------------------------------
@bp.route("<int:email_id>/delete", methods=["POST"], strict_slashes=False)
@login_required
def delete_email(email_id):
    """
    Handle the deletion of a secure email message for the current user.

    Retrieves a message identified by the email_id parameter,
    and deletes it from the database if it belongs to the current user.
    On successful deletion, a success message is flashed, and the user
    is redirected to the secure email message index page.

    Args:
        email_id (int): The ID of the message to be deleted.

    Returns:
        Response: A redirect response to the secure email message index page.
    """
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        db.session.delete(email)  # ✅ fixed
        db.session.commit()
        flash(_("Message deleted."), "success")
        log_info_message(f"User '{current_user.username}' deleted email message ID={email_id}.")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("delete_email failed", e)
        flash(_("An error occurred while deleting the message."), "danger")

    return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Attach files to a message
# ---------------------------------------------------------------------
@bp.route("<int:message_id>/files", methods=["GET", "POST"], strict_slashes=False)
@login_required
def attach_files(message_id):
    """
    View to attach files to a message.

    :param int message_id: ID of the message to attach files to.
    """
    try:
        message = EmailMessage.query.filter_by(
            id=message_id, user_id=current_user.id
        ).first_or_404()
        existing = {f.file_path for f in message.files}

        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "uploads"))
        available_files = list_available_files(upload_dir)

        form = AttachFilesForm()  # Ensure form is initialized

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

            # Determine the template to render based on the request type (HTMX or not)
            template = (
                "email/attach_files_partial.html"  # Partial view for HTMX requests
                if request.headers.get("HX-Request")
                else "email/attach_files_full.html"  # Full view for regular requests
            )
            return render_template(
                template,
                message=message,
                form=form,
                available_files=available_files,
                existing_files=existing,
            )

        # If it's a GET request, render the page
        template = (
            "email/attach_files_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "email/attach_files_full.html"  # Full view for regular requests
        )

        return render_template(
            template,
            message=message,
            form=form,
            available_files=available_files,
            existing_files=existing,
        )

    except Exception as e:
        log_exception_with_traceback("attach_files error", e)
        flash(_("An unexpected error occurred while loading attachments."), "danger")
        return render_template("error.html"), 500  # Ensure the error page exists


# ---------------------------------------------------------------------
# View message + SMTP config + attachments
# ---------------------------------------------------------------------
@bp.route("<int:email_id>/view", methods=["GET"], strict_slashes=False)
@login_required
def view_email_config(email_id):
    """
    View the configuration of a message.

    Displays the message details, SMTP configuration,
    and any attachments associated with the message.

    :param int email_id: ID of the message to view.
    """
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()
        log_info_message(f"User '{current_user.username}' viewed config for email ID={email_id}.")

        # Determine if the request is an HTMX request
        template = (
            "email/view_email_config_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "email/view_email_config_full.html"  # Full view for normal requests
        )

        return render_template(template, message=email, smtp=smtp)  # ✅ fixed
    except Exception as e:
        log_exception_with_traceback("view_email_config failed", e)
        flash(_("An error occurred while loading the message configuration."), "danger")
        return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Send test email (via Apprise CLI)
# ---------------------------------------------------------------------
@bp.route("<int:email_id>/send-test", methods=["POST"], strict_slashes=False)
@login_required
def send_test_email(email_id):
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        smtp = email.smtp_configs[0] if email.smtp_configs else None  # ✅ fixed variable name

        if not smtp or not smtp.enabled:
            flash(_("SMTP configuration not assigned or is disabled."), "danger")
            return redirect(url_for("email.view_email_config", email_id=email.id))  # ✅ fixed

        decrypted_password = smtp.smtp_password

        apprise_url = (
            f"mailtos://{current_user.email}"
            f"?smtp={smtp.smtp_host}"
            f"&user={smtp.smtp_username}"
            f"&pass={decrypted_password}"
            f"&secure=starttls"
        )

        cmd = [
            "apprise",
            "--title",
            email.subject,  # ✅ fixed
            "--body",
            email.body,  # ✅ fixed
        ]
        for f in email.files:  # ✅ fixed
            cmd += ["--attach", os.path.join("uploads", f.file_path)]
        cmd.append(apprise_url)

        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        flash(_("Test email sent successfully."), "success")
        log_info_message(
            f"User '{current_user.username}' sent test email for message ID={email_id}."
        )

    except subprocess.CalledProcessError as e:
        reason = e.stderr or e.stdout or _("Unknown error")
        flash(_("Email failed: %(reason)s", reason=reason), "danger")
        log_info_message(
            f"User '{current_user.username}' failed to send test email ID={email_id}: {e}"
        )

    except Exception as e:
        flash(_("An unexpected error occurred while sending test email."), "danger")
        log_exception_with_traceback("Unhandled error in send_test_email()", e)

    return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Email Schedule (Check-in & Grace Period)
# ---------------------------------------------------------------------
@bp.route("schedule/<int:email_id>", methods=["GET", "POST"], strict_slashes=False)
@login_required
def schedule_email(email_id):
    """
    Handles scheduling of a secure email.

    Allows the user to edit the scheduling of a secure email, including
    the check-in interval and grace period. The user must be the owner of
    the secure email to be able to edit it.

    :param email_id: The ID of the secure email message to be edited.
    :returns: Redirects to the list of secure email messages with a success
        or error flash message.
    """
    try:
        email = db.session.get(EmailMessage, email_id)
        if not email:
            abort(404)

        if email.user_id != current_user.id:
            flash(_("Access denied."), "danger")
            return redirect(url_for("email.index"))

        form = ScheduleForm()

        if request.method == "GET":
            if email.checkin_interval_minutes:
                load_minutes_into_form_parts(form, "checkin", email.checkin_interval_minutes)
            if email.grace_period_minutes:
                load_minutes_into_form_parts(form, "grace", email.grace_period_minutes)

        if form.validate_on_submit():
            email.checkin_interval_minutes = total_minutes_from_form_parts(form, "checkin")
            email.grace_period_minutes = total_minutes_from_form_parts(form, "grace")
            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' updated schedule for email ID={email_id}."
            )
            flash(_("Schedule updated successfully."), "success")
            return redirect(url_for("email.index"))

        # Determine if the request is an HTMX request
        template = (
            "email/schedule_email_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "email/schedule_email_full.html"  # Full view for regular requests
        )

        return render_template(
            template,
            form=form,
            message=email,
        )

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("schedule update failed", e)
        flash(_("An error occurred while updating the schedule."), "danger")
        return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Email SMTP Configuration Assignment
# ---------------------------------------------------------------------
@bp.route("<int:email_id>/smtp", methods=["GET", "POST"], strict_slashes=False)
@login_required
def assign_smtp_to_email(email_id):
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        smtp_options = UserMailSettings.query.filter_by(user_id=current_user.id).all()
        form = AssignSmtpForm()

        if request.method == "POST" and form.validate_on_submit():
            selected_id = request.form.get("smtp_config")
            if selected_id:
                selected = UserMailSettings.query.filter_by(
                    id=selected_id, user_id=current_user.id
                ).first()
                if selected:
                    email.smtp_configs = [selected]
                    db.session.commit()
                    log_info_message(
                        f"User '{current_user.username}' assigned SMTP config ID={selected_id} to email ID={email_id}."
                    )
                    flash(_("SMTP configuration assigned."), "success")
                    return redirect(url_for("email.index"))
            else:
                email.smtp_configs = []
                db.session.commit()
                log_info_message(
                    f"User '{current_user.username}' unassigned SMTP config from email ID={email_id}."
                )
                flash(_("SMTP configuration removed."), "info")
                return redirect(url_for("email.index"))

        # Determine if the request is an HTMX request
        template = (
            "email/assign_smtp_to_email_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "email/assign_smtp_to_email_full.html"  # Full view for regular requests
        )

        return render_template(template, message=email, smtp_options=smtp_options, form=form)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("assign_smtp_to_email failed", e)
        flash(_("An error occurred while assigning SMTP configuration."), "danger")
        return redirect(url_for("email.index"))


# ---------------------------------------------------------------------
# Email Status
# ---------------------------------------------------------------------
@bp.route("status", methods=["GET"], strict_slashes=False)
@login_required
def email_status():
    """
    API endpoint to return the list of emails and their current enabled status
    for the logged-in user. Used for UI polling to refresh enabled/disabled states.
    """
    try:
        emails = EmailMessage.query.filter_by(user_id=current_user.id).all()
        email_status_list = [{"id": email.id, "is_enabled": email.is_enabled} for email in emails]
        log_info_message(f"User '{current_user.username}' polled email status.")
        return jsonify(email_status_list)
    except Exception as e:
        log_exception_with_traceback("email_status polling failed", e)
        return jsonify({"error": _("Unable to fetch email status.")}), 500
