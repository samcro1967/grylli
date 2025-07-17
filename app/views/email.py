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
from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
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
from app.utils.logging import (
    log_debug_message,
    log_exception_with_traceback,
    log_info_message,
    log_user_action,
)

bp = Blueprint("email", __name__)


@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
def index():
    try:
        emails = (
            db.session.query(EmailMessage)
            .filter_by(user_id=current_user.id)
            .order_by(EmailMessage.created_at.desc())
            .all()
        )
        log_info_message(f"Access - {current_user.username} - Emails")

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


@bp.route("create", methods=["GET", "POST"], strict_slashes=False)
@bp.route("<int:email_id>/edit", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_email(email_id=None):
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
            log_user_action("Email", "Edit", email, current_user.username)
            flash(_("Message saved."), "success")

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


@bp.route("<int:email_id>/delete", methods=["POST"], strict_slashes=False)
@login_required
def delete_email(email_id):
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()

        log_user_action("Email", "Delete", email, current_user.username)

        db.session.delete(email)
        db.session.commit()
        flash(_("Message deleted."), "success")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("delete_email failed", e)
        flash(_("An error occurred while deleting the message."), "danger")

    return redirect(url_for("email.index"))


@bp.route("<int:message_id>/files", methods=["GET", "POST"], strict_slashes=False)
@login_required
def attach_files(message_id):
    try:
        message = EmailMessage.query.filter_by(
            id=message_id, user_id=current_user.id
        ).first_or_404()
        existing = {f.file_path for f in message.files}
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "uploads"))
        available_files = list_available_files(upload_dir)
        form = AttachFilesForm()

        if request.method == "POST":
            selected = request.form.getlist("file_paths")
            message.files.clear()
            for f in selected:
                message.files.append(EmailFileLink(file_path=f))
            db.session.commit()
            db.session.refresh(message)
            file_labels = [f.file_path for f in message.files]
            log_user_action(
                "Email",
                "Attach",
                message,
                current_user.username,
                extra=", ".join(file_labels) if file_labels else "No files",
            )
            flash(_("Attached files updated."), "success")
            return redirect(url_for("email.index"))

        template = (
            "email/attach_files_partial.html"
            if request.headers.get("HX-Request")
            else "email/attach_files_full.html"
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
        return render_template("error.html"), 500


@bp.route("<int:email_id>/view", methods=["GET"], strict_slashes=False)
@login_required
def view_email_config(email_id):
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()

        log_user_action("Email", "View", email, current_user.username)

        template = (
            "email/view_email_config_partial.html"
            if request.headers.get("HX-Request")
            else "email/view_email_config_full.html"
        )
        return render_template(template, message=email, smtp=smtp)
    except Exception as e:
        log_exception_with_traceback("view_email_config failed", e)
        flash(_("An error occurred while loading the message configuration."), "danger")
        return redirect(url_for("email.index"))


@bp.route("<int:email_id>/send-test", methods=["POST"], strict_slashes=False)
@login_required
def send_test_email(email_id):
    try:
        email = EmailMessage.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        smtp = email.smtp_configs[0] if email.smtp_configs else None

        if not smtp or not smtp.enabled:
            flash(_("SMTP configuration not assigned or is disabled."), "danger")
            return redirect(url_for("email.view_email_config", email_id=email.id))

        decrypted_password = smtp.smtp_password

        apprise_url = f"mailtos://{current_user.email}?smtp={smtp.smtp_host}&user={smtp.smtp_username}&pass={decrypted_password}&secure=starttls"

        cmd = ["apprise", "--title", email.subject, "--body", email.body]
        for f in email.files:
            cmd += ["--attach", os.path.join("uploads", f.file_path)]
        cmd.append(apprise_url)

        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        log_user_action("Email", "Send Test", email, current_user.username)
        flash(_("Test email sent successfully."), "success")

    except subprocess.CalledProcessError as e:
        reason = e.stderr or e.stdout or _("Unknown error")
        flash(_("Email failed: %(reason)s", reason=reason), "danger")
        log_info_message(f"Test email failed for '{current_user.username}': {reason}")
    except Exception as e:
        flash(_("An unexpected error occurred while sending test email."), "danger")
        log_exception_with_traceback("Unhandled error in send_test_email()", e)

    return redirect(url_for("email.index"))


@bp.route("schedule/<int:email_id>", methods=["GET", "POST"], strict_slashes=False)
@login_required
def schedule_email(email_id):
    try:
        email = db.session.get(EmailMessage, email_id)
        if not email or email.user_id != current_user.id:
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
            log_user_action(
                "Email",
                "Set Schedule",
                email,
                current_user.username,
                extra=f"checkin={email.checkin_interval_minutes}min, grace={email.grace_period_minutes}min",
            )
            flash(_("Schedule updated successfully."), "success")
            return redirect(url_for("email.index"))

        template = (
            "email/schedule_email_partial.html"
            if request.headers.get("HX-Request")
            else "email/schedule_email_full.html"
        )

        return render_template(template, form=form, message=email)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("schedule update failed", e)
        flash(_("An error occurred while updating the schedule."), "danger")
        return redirect(url_for("email.index"))


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
                    log_user_action(
                        "Email", "Assign", email, current_user.username, extra=selected.label
                    )
                    flash(_("SMTP configuration assigned."), "success")
                    return redirect(url_for("email.index"))
            else:
                email.smtp_configs = []
                db.session.commit()
                log_user_action("Email", "Detach", email, current_user.username)
                flash(_("SMTP configuration removed."), "info")
                return redirect(url_for("email.index"))

        template = (
            "email/assign_smtp_to_email_partial.html"
            if request.headers.get("HX-Request")
            else "email/assign_smtp_to_email_full.html"
        )

        return render_template(template, message=email, smtp_options=smtp_options, form=form)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("assign_smtp_to_email failed", e)
        flash(_("An error occurred while assigning SMTP configuration."), "danger")
        return redirect(url_for("email.index"))


@bp.route("status", methods=["GET"], strict_slashes=False)
@login_required
def email_status():
    try:
        emails = EmailMessage.query.filter_by(user_id=current_user.id).all()
        email_status_list = [{"id": email.id, "is_enabled": email.is_enabled} for email in emails]
        log_debug_message(f"Email status polled by '{current_user.username}'")
        return jsonify(email_status_list)
    except Exception as e:
        log_exception_with_traceback("email_status polling failed", e)
        return jsonify({"error": _("Unable to fetch email status.")}), 500
