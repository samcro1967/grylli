from datetime import datetime
import os
import subprocess

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from cryptography.fernet import InvalidToken
from flask_babel import _

from app.forms.secure_email_forms import EmailMessageForm, UserMailSettingsForm, AttachFilesForm
from app.forms.message_form import ScheduleForm
from app.models import db, EmailMessage, UserMailSettings, EmailFileLink
from app.services.encryption import encrypt, decrypt
from app.utils.duration import total_minutes_from_form_parts, load_minutes_into_form_parts
from app.utils.file_utils import list_available_files

bp = Blueprint("secure_email_bp", __name__)

# ---------------------------------------------------------------------
# List all secure email messages
# ---------------------------------------------------------------------
@bp.route("/emails")
@login_required
def index():
    emails = EmailMessage.query.filter_by(user_id=current_user.id).all()
    return render_template("secure_email/list_emails.html", emails=emails)

# ---------------------------------------------------------------------
# Create or edit a secure email message
# ---------------------------------------------------------------------
@bp.route("/create", methods=["GET", "POST"])
@bp.route("/emails/<int:message_id>/edit", methods=["GET", "POST"])
@login_required
def edit_message(message_id=None):
    if message_id:
        message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
        form = EmailMessageForm(obj=message)
    else:
        message = EmailMessage(user_id=current_user.id)
        form = EmailMessageForm()

    if form.validate_on_submit():
        form.populate_obj(message)
        db.session.add(message)
        db.session.commit()
        flash("Message saved.", "success")
        return redirect(url_for("secure_email_bp.index"))

    return render_template("secure_email/edit_message.html", form=form, message=message)
# ---------------------------------------------------------------------
# Delete a secure email message
# ---------------------------------------------------------------------
@bp.route("/emails/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("secure_email_bp.index"))

# ---------------------------------------------------------------------
# Configure SMTP settings
# ---------------------------------------------------------------------


@bp.route("/smtp_settings", methods=["GET", "POST"])
@login_required
def smtp_settings():
    settings = UserMailSettings.query.filter_by(user_id=current_user.id).first()
    form = UserMailSettingsForm()

    if request.method == "GET":
        if settings:
            form.smtp_host.data = settings.smtp_host
            form.smtp_port.data = settings.smtp_port
            form.smtp_username.data = settings.smtp_username
            form.use_tls.data = settings.use_tls
            form.enabled.data = settings.enabled

            # Mask password if one is stored
            if settings and settings.smtp_password:
                try:
                    form.smtp_password.data = decrypt(settings.smtp_password)
                except InvalidToken:
                    form.smtp_password.data = ""
                    flash("⚠️ Failed to decrypt saved SMTP password. Please re-enter.", "danger")

    if form.validate_on_submit():
        if not settings:
            settings = UserMailSettings(user_id=current_user.id)

        settings.smtp_host = form.smtp_host.data
        settings.smtp_port = form.smtp_port.data
        settings.smtp_username = form.smtp_username.data
        settings.use_tls = form.use_tls.data
        settings.enabled = form.enabled.data

        # Only update password if changed from masked
        new_pw = form.smtp_password.data
        if new_pw != "********":
            settings.smtp_password = encrypt(new_pw)  # Ensure secure storage

        db.session.add(settings)
        db.session.commit()

        flash(_("✅ SMTP settings saved."), "success")
        return redirect(url_for("secure_email_bp.smtp_settings"))

    return render_template("secure_email/smtp_settings.html", form=form)

# ---------------------------------------------------------------------
# Attach files to a message
# ---------------------------------------------------------------------
@bp.route("/emails/<int:message_id>/files", methods=["GET", "POST"])
@login_required
def attach_files(message_id):
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    existing = {f.file_path for f in message.files}

    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "uploads"))
    available_files = list_available_files(upload_dir)

    if request.method == "POST":
        selected = request.form.getlist("file_paths")
        message.files.clear()
        for f in selected:
            message.files.append(EmailFileLink(file_path=f))
        db.session.commit()
        flash("Attached files updated.", "success")
        return redirect(url_for("secure_email_bp.index"))

    return render_template("secure_email/attach_files.html", message=message,
                           available_files=available_files, existing_files=existing)

# ---------------------------------------------------------------------
# View message + SMTP config + attachments
# ---------------------------------------------------------------------
@bp.route("/emails/<int:message_id>/view", methods=["GET"])
@login_required
def view_config(message_id):
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()
    return render_template("secure_email/view_config.html", message=message, smtp=smtp)

# ---------------------------------------------------------------------
# Send test email (via Apprise CLI)
# ---------------------------------------------------------------------
@bp.route("/emails/<int:message_id>/send-test", methods=["POST"])
@login_required
def send_test(message_id):
    message = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()

    if not smtp or not smtp.enabled:
        flash("SMTP not configured or disabled.", "danger")
        return redirect(url_for("secure_email_bp.view_config", message_id=message.id))

    try:
        decrypted_password = decrypt(smtp.smtp_password)
    except Exception:
        flash("Failed to decrypt SMTP password. Please re-enter it.", "danger")
        return redirect(url_for("secure_email_bp.view_config", message_id=message.id))

    # Build the Apprise URL
    apprise_url = (
        f"mailtos://{current_user.email}"
        f"?smtp={smtp.smtp_host}"
        f"&user={smtp.smtp_username}"
        f"&pass={decrypted_password}"
        f"&secure=starttls"
    )

    cmd = [
        "apprise",
        "--title", message.subject,
        "--body", message.body,
    ]

    for f in message.files:
        cmd += ["--attach", os.path.join("uploads", f.file_path)]

    cmd.append(apprise_url)

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        flash("Test email sent successfully.", "success")
    except subprocess.CalledProcessError as e:
        print("📤 STDOUT:", e.stdout)
        print("📤 STDERR:", e.stderr)
        flash(f"Email failed: {e.stderr or e.stdout or 'Unknown error'}", "danger")

    return redirect(url_for("secure_email_bp.index", message_id=message.id))

# ---------------------------------------------------------------------
# Send test SMTP email with dummy content (via Apprise CLI)
# ---------------------------------------------------------------------
@bp.route("/emails/settings/send-test", methods=["POST"])
@login_required
def send_smtp_test():
    smtp = UserMailSettings.query.filter_by(user_id=current_user.id).first()
    if not smtp or not smtp.enabled:
        flash("SMTP not configured or disabled.", "danger")
        return redirect(url_for("secure_email_bp.smtp_settings"))

    try:
        decrypted_password = decrypt(smtp.smtp_password)
    except Exception:
        flash("Failed to decrypt SMTP password. Please re-enter it.", "danger")
        return redirect(url_for("secure_email_bp.smtp_settings"))

    apprise_url = (
        f"mailtos://{current_user.email}"
        f"?smtp={smtp.smtp_host}"
        f"&user={smtp.smtp_username}"
        f"&pass={decrypted_password}"
        f"&secure=starttls"
    )

    cmd = [
        "apprise",
        "--title", "SMTP Test Email",
        "--body", "This is a test of your SMTP configuration in Grylli.",
        apprise_url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        flash("SMTP test email sent to your address.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"SMTP test failed: {e.stderr or e.stdout}", "danger")

    return redirect(url_for("secure_email_bp.smtp_settings"))

# ---------------------------------------------------------------------
# Email Schedule
# ---------------------------------------------------------------------
@bp.route("/emails/schedule/<int:message_id>", methods=["GET", "POST"])
@login_required
def schedule(message_id):
    message = EmailMessage.query.get_or_404(message_id)

    if message.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("secure_email_bp.index"))

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
        flash("Schedule updated successfully.", "success")
        return redirect(url_for("secure_email_bp.index"))

    return render_template("secure_email/schedule_email.html", form=form, message=message)

# ---------------------------------------------------------------------
# Help function tto decrypt and construct the apprise URL
# ---------------------------------------------------------------------
def build_apprise_url(email_to, smtp_settings):
    password = decrypt(smtp_settings.smtp_password)
    return (
        f"mailtos://{email_to}"
        f"?smtp={smtp_settings.smtp_host}"
        f"&user={smtp_settings.smtp_username}"
        f"&pass={password}"
        f"&secure=starttls"
    )
