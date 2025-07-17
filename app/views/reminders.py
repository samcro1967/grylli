# ---------------------------------------------------------------------
# reminders.py
# app/views/reminders.py
# Routes for managing user reminders (create, edit, list, delete, destinations).
# ---------------------------------------------------------------------

import os
import subprocess
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm

from app.extensions import db
from app.forms.reminder_form import EmailReminderLinkForm, ReminderForm, ScheduleReminderForm
from app.models import AppriseURL, EmailMessage, Reminder, UserMailSettings, Webhook
from app.services.apprise_utils import send_test_apprise_notification
from app.services.mail import send_email
from app.services.webhook import send_test_webhook_notification
from app.utils.logging import (
    log_debug_message,
    log_exception_with_traceback,
    log_info_message,
    log_user_action,
)

bp = Blueprint("reminders_bp", __name__)


class DummyForm(FlaskForm):
    pass


# ---------------------------------------------------------------------
# View: List Reminders
# ---------------------------------------------------------------------
@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
def overview():
    try:
        reminders = (
            db.session.query(Reminder)
            .filter_by(user_id=current_user.id)
            .order_by(Reminder.created_at.desc())
            .all()
        )
        now = datetime.now()
        log_info_message(f"Access - {current_user.username} - Reminders")
        log_debug_message(f"Loaded {len(reminders)} reminders for {current_user.username}")

        template = (
            "reminders/list_reminders_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/list_reminders_full.html"
        )
        return render_template(template, reminders=reminders, now=now)

    except Exception as e:
        log_exception_with_traceback("Error loading reminders list", e)
        flash(_("Failed to load reminders."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# View: Create Reminder
# ---------------------------------------------------------------------
@bp.route("create/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def create_reminder():
    log_info_message(f"Access - {current_user.username} - Create Reminder")

    form = ReminderForm()
    try:
        if form.validate_on_submit():
            now = datetime.now(timezone.utc)
            reminder = Reminder(
                user_id=current_user.id,
                label=form.label.data.strip(),
                subject=form.subject.data.strip(),
                content=form.content.data.strip(),
                start_at=datetime(2000, 1, 1),  # placeholder until scheduled
                is_enabled=True,
                created_at=now,
                updated_at=now,
            )
            db.session.add(reminder)
            db.session.commit()

            log_user_action("Reminder", "Create", reminder)
            flash(_("Reminder created successfully."), "success")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "reminderListChanged"
                return response

            return redirect(url_for("reminders_bp.overview"))

        if request.method == "POST":
            log_debug_message(
                f"Form validation failed creating reminder for {current_user.username}"
            )

        template = (
            "reminders/reminder_form_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/create_reminder_full.html"
        )
        return render_template(template, form=form)

    except Exception as e:
        log_exception_with_traceback("Error creating reminder", e)
        flash(_("Failed to create reminder."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Edit Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/edit/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - Edit Reminder")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        form = ReminderForm(obj=reminder)

        if form.validate_on_submit():
            reminder.label = form.label.data.strip()
            reminder.subject = form.subject.data.strip()
            reminder.content = form.content.data.strip()
            db.session.commit()

            log_user_action("Reminder", "Edit", reminder)
            flash(_("Reminder updated successfully."), "success")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "reminderListChanged"
                return response

            return redirect(url_for("reminders_bp.overview"))

        if request.method == "POST":
            log_debug_message(
                f"Form validation failed for editing reminder ID={reminder.id} by {current_user.username}"
            )

        template = (
            "reminders/reminder_form_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/edit_reminder.html"
        )
        return render_template(template, form=form, reminder=reminder)

    except Exception as e:
        log_exception_with_traceback(f"Error editing reminder ID={reminder_id}", e)
        flash(_("Failed to edit reminder."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Delete Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/delete/", methods=["POST"], strict_slashes=False)
@login_required
def delete_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - Delete Reminder")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            log_debug_message(
                f"Delete denied for reminder ID={reminder_id} (unauthorized or not found)"
            )
            abort(404)

        db.session.delete(reminder)
        db.session.commit()

        log_user_action("Reminder", "Delete", reminder)
        flash(_("Reminder deleted."), "success")
    except Exception as e:
        log_exception_with_traceback(f"Error deleting reminder ID={reminder_id}", e)
        flash(_("Failed to delete reminder."), "danger")

    return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Assign Destinations (Apprise, Webhook, SMTP)
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/destinations/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def assign_destinations(reminder_id):
    log_info_message(f"Access - {current_user.username} - Assign Destinations")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        form = DummyForm()

        apprise_options = (
            AppriseURL.query.filter_by(user_id=current_user.id, enabled=True)
            .order_by(AppriseURL.label)
            .all()
        )
        webhook_options = (
            Webhook.query.filter_by(user_id=current_user.id, enabled=True)
            .order_by(Webhook.label)
            .all()
        )
        smtp_options = (
            UserMailSettings.query.filter_by(user_id=current_user.id, enabled=True)
            .order_by(UserMailSettings.label)
            .all()
        )

        if request.method == "POST" and form.validate_on_submit():
            selected_apprise_ids = request.form.getlist("apprise_destinations")
            selected_webhook_ids = request.form.getlist("webhooks")
            selected_smtp_id = request.form.get("smtp_config")

            reminder.apprise_destinations = [
                a for a in apprise_options if str(a.id) in selected_apprise_ids
            ]
            reminder.webhooks = [w for w in webhook_options if str(w.id) in selected_webhook_ids]

            if selected_smtp_id:
                reminder.smtp_configs = [s for s in smtp_options if str(s.id) == selected_smtp_id]
            else:
                reminder.smtp_configs = []

            db.session.commit()
            log_user_action("Reminder", "Assign", reminder)
            flash(_("Destinations updated."), "success")
            return redirect(url_for("reminders_bp.overview"))

        template = (
            "reminders/assign_destinations_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/assign_destinations_full.html"
        )

        return render_template(
            template,
            form=form,
            reminder=reminder,
            apprise_options=apprise_options,
            webhook_options=webhook_options,
            smtp_options=smtp_options,
        )

    except Exception as e:
        log_exception_with_traceback(
            f"Error assigning destinations for reminder ID={reminder_id}", e
        )
        flash(_("Failed to load or update destinations."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Test Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/send-test", methods=["POST"], strict_slashes=False)
@login_required
def send_test_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - Send Test Reminder")

    try:
        reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()

        if not (reminder.apprise_destinations or reminder.webhooks or reminder.smtp_configs):
            flash(_("No destinations assigned to this reminder."), "danger")
            return redirect(url_for("reminders_bp.overview"))

        success = True
        errors = []

        for apprise in reminder.apprise_destinations:
            ok, msg = send_test_apprise_notification(apprise.url)
            if not ok:
                errors.append(f"Apprise ({apprise.label}): {msg}")
                log_info_message(
                    f"User '{current_user.username}' failed Apprise test for reminder ID={reminder.id} via '{apprise.label}': {msg}"
                )
                success = False

        for webhook in reminder.webhooks:
            ok, msg = send_test_webhook_notification(webhook.endpoint)
            if not ok:
                errors.append(f"Webhook ({webhook.label}): {msg}")
                log_info_message(
                    f"User '{current_user.username}' failed Webhook test for reminder ID={reminder.id} via '{webhook.label}': {msg}"
                )
                success = False

        for smtp in reminder.smtp_configs:
            try:
                email_msg = reminder.email_messages[0] if reminder.email_messages else None
                if not email_msg:
                    raise Exception(_("No email message linked to this reminder."))
                if not smtp.enabled:
                    raise Exception(_("SMTP configuration is disabled."))

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
                    "[TEST] " + email_msg.subject,
                    "--body",
                    email_msg.body,
                ]
                for f in email_msg.files:
                    cmd += ["--attach", os.path.join("uploads", f.file_path)]

                cmd.append(apprise_url)
                subprocess.run(cmd, capture_output=True, check=True, text=True)

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr or e.stdout or "Unknown error"
                errors.append(f"SMTP ({smtp.label}): {error_msg}")
                log_info_message(
                    f"User '{current_user.username}' failed SMTP Apprise test for reminder ID={reminder.id} via '{smtp.label}': {error_msg}"
                )
                success = False
            except Exception as e:
                errors.append(f"SMTP ({smtp.label}): {str(e)}")
                log_info_message(
                    f"User '{current_user.username}' encountered SMTP error for reminder ID={reminder.id} via '{smtp.label}': {str(e)}"
                )
                success = False

        if success:
            flash(_("Test reminder sent successfully."), "success")
            log_user_action("Reminder", "Send Test", reminder)
        else:
            flash(_("Test reminder failed: ") + "; ".join(errors), "danger")
            log_info_message(
                f"User '{current_user.username}' failed test reminder ID={reminder.id}. Errors: {'; '.join(errors)}"
            )

    except Exception as e:
        log_exception_with_traceback(f"Unexpected error in send_test_reminder ID={reminder_id}", e)
        flash(_("Failed to send test reminder."), "danger")

    return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View Deatils
# ---------------------------------------------------------------------
@bp.route("view/<int:reminder_id>", strict_slashes=False)
@login_required
def view_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - View Reminder")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        log_user_action("Reminder", "View", reminder)

        template = (
            "reminders/view_reminder_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/view_reminder_full.html"
        )

        return render_template(template, reminder=reminder)

    except Exception as e:
        log_exception_with_traceback(f"Error viewing reminder ID={reminder_id}", e)
        flash(_("Failed to load reminder details."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Schedule Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/schedule/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def schedule_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - Schedule Reminder")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        form = ScheduleReminderForm(obj=reminder)

        if form.validate_on_submit():
            reminder.start_at = form.start_at.data
            reminder.recurrence_rule = form.recurrence_rule.data
            reminder.end_at = form.end_at.data
            reminder.max_occurrences = form.max_occurrences.data
            db.session.commit()
            log_user_action("Reminder", "Set Schedule", reminder)
            flash(_("Reminder schedule updated successfully."), "success")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "reminderListChanged"
                return response

            return redirect(url_for("reminders_bp.overview"))

        template = (
            "reminders/schedule_reminder_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/schedule_reminder_full.html"
        )

        interval_minutes = current_app.config.get("SCHEDULER_REMINDER_INTERVAL_MINUTES", 15)
        log_debug_message(f"Rendering schedule form for reminder ID={reminder.id} (Interval={interval_minutes} min)")
        return render_template(template, form=form, reminder=reminder, interval_minutes=interval_minutes)

    except Exception as e:
        log_exception_with_traceback(f"Error scheduling reminder ID={reminder_id}", e)
        flash(_("Failed to load or save reminder schedule."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Email association
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/email/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def assign_email_to_reminder(reminder_id):
    log_info_message(f"Access - {current_user.username} - Assign Email to Reminder")

    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        form = EmailReminderLinkForm()

        smtp_configs = UserMailSettings.query.filter_by(user_id=current_user.id, enabled=True).all()
        email_messages = EmailMessage.query.filter_by(user_id=current_user.id).all()

        form.smtp_config.choices = [("none", _("None"))] + [
            (str(s.id), s.label) for s in smtp_configs
        ]
        form.message.choices = [("none", _("None"))] + [
            (str(m.id), m.label) for m in email_messages
        ]

        smtp_config_map = {str(s.id): s for s in smtp_configs}
        email_messages_map = {str(m.id): m for m in email_messages}

        if request.method == "GET":
            if reminder.smtp_configs:
                form.smtp_config.data = str(reminder.smtp_configs[0].id)
            else:
                form.smtp_config.data = "none"

            if reminder.email_messages:
                form.message.data = str(reminder.email_messages[0].id)
            else:
                form.message.data = "none"

        if form.validate_on_submit():
            smtp_selected = form.smtp_config.data != "none"
            msg_selected = form.message.data != "none"

            if smtp_selected != msg_selected:
                flash(
                    _("You must select both an SMTP config and an email message, or neither."),
                    "warning",
                )
            else:
                reminder.smtp_configs = (
                    [s for s in smtp_configs if str(s.id) == form.smtp_config.data]
                    if smtp_selected
                    else []
                )
                reminder.email_messages = (
                    [EmailMessage.query.get(int(form.message.data))] if msg_selected else []
                )

                db.session.commit()
                log_user_action("Reminder", "Assign", reminder, extra="Email")
                flash(_("Email reminder settings updated."), "success")

                if request.headers.get("HX-Request"):
                    response = make_response("", 204)
                    response.headers["HX-Trigger"] = "reminderListChanged"
                    return response

                return redirect(url_for("reminders_bp.overview"))

        template = (
            "reminders/assign_email_reminder_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/assign_email_reminder_full.html"
        )

        log_debug_message(f"Rendering email assignment form for reminder ID={reminder.id}")
        return render_template(
            template,
            form=form,
            reminder=reminder,
            smtp_config_map=smtp_config_map,
            email_messages_map=email_messages_map,
        )
    except Exception as e:
        log_exception_with_traceback(f"Error assigning email to reminder ID={reminder_id}", e)
        flash(_("Failed to assign email reminder."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Reminder Status
# --------------------------------------------------------------
@bp.route("status", methods=["GET"], strict_slashes=False)
@login_required
def reminder_status():
    """
    View: Reminder Status
    ======================

    This view returns a JSON array of reminder objects, each containing
    only the reminder ID and whether the reminder is enabled or not.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Reminder Status JSON")

        reminders = Reminder.query.filter_by(user_id=current_user.id).all()
        log_debug_message(f"Returning reminder status JSON with {len(reminders)} reminders")

        return jsonify([{"id": r.id, "is_enabled": r.is_enabled} for r in reminders])
    except Exception as e:
        log_exception_with_traceback("Error retrieving reminder status JSON", e)
        return jsonify({"error": "Failed to retrieve reminder status."}), 500
