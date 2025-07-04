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
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("reminders_bp", __name__)


class DummyForm(FlaskForm):
    pass


# ---------------------------------------------------------------------
# View: List Reminders
# ---------------------------------------------------------------------
@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
def overview():
    """
    View: List Reminders
    ====================

    Displays a list of reminders for the current user.

    - Renders full layout for normal requests
    - Renders partial for HTMX requests
    """
    try:
        reminders = (
            db.session.query(Reminder)
            .filter_by(user_id=current_user.id)
            .order_by(Reminder.created_at.desc())
            .all()
        )
        now = datetime.now()
        log_info_message(f"User '{current_user.username}' viewed their reminders list.")

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
    """
    View: Create Reminder (HTMX-compatible)
    """
    log_info_message(
        f"[DEBUG TEST] current_user in create_reminder: {current_user} (id={getattr(current_user, 'id', 'None')})"
    )

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
            log_info_message(
                f"User '{current_user.username}' created reminder '{reminder.label}' (ID={reminder.id})."
            )
            flash(_("Reminder created successfully."), "success")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "reminderListChanged"
                return response

            return redirect(url_for("reminders_bp.overview"))

        template = (
            "reminders/reminder_form_partial.html"
            if request.headers.get("HX-Request")
            else "reminders/create_reminder_full.html"
        )
        return render_template(template, form=form)

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback("Error creating reminder", e)
        flash(_("Failed to create reminder."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Edit Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/edit/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_reminder(reminder_id):
    """
    View: Edit Reminder (HTMX-compatible)
    ================================

    This view handles editing an existing reminder. If the request is made via HTMX,
    it will update the main content without refreshing the sidebar. If the request
    is not made via HTMX, it will render the full page.

    :param int reminder_id: The ID of the reminder to edit.
    :return: A rendered template of reminders/edit_reminder.html.
    :rtype: flask.Response
    """
    try:
        # Fetch the reminder to edit
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        form = ReminderForm(obj=reminder)

        if form.validate_on_submit():
            # Update reminder fields based on the form data
            reminder.label = form.label.data.strip()
            reminder.subject = form.subject.data.strip()
            reminder.content = form.content.data.strip()
            db.session.commit()
            log_info_message(f"User '{current_user.username}' edited reminder ID={reminder.id}.")
            flash(_("Reminder updated successfully."), "success")

            # Handle HTMX request (without reloading the sidebar)
            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = (
                    "reminderListChanged"  # Trigger an update to reminder list
                )
                return response

            # If not an HTMX request, redirect to the list of reminders (overview)
            return redirect(url_for("reminders_bp.overview"))

        # If the form hasn't been submitted yet, render the edit form
        template = (
            "reminders/reminder_form_partial.html"  # HTMX-compatible partial (for HTMX requests)
            if request.headers.get("HX-Request")
            else "reminders/edit_reminder.html"  # Full page render
        )
        return render_template(template, form=form, reminder=reminder)

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback(f"Error editing reminder ID={reminder_id}", e)
        flash(_("Failed to edit reminder."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Delete Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/delete/", methods=["POST"], strict_slashes=False)
@login_required
def delete_reminder(reminder_id):
    """
    View: Delete Reminder
    =================

    This view handles deleting an existing reminder.

    The reminder ID is passed as a parameter and the reminder is deleted from
    the database. If the reminder is not found or does not belong to the
    current user, a 404 error is raised.

    :param int reminder_id: The ID of the reminder to delete.
    :return: A redirect to the list of reminders.
    :rtype: flask.Response
    """
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        db.session.delete(reminder)
        db.session.commit()
        log_info_message(f"User '{current_user.username}' deleted reminder ID={reminder.id}.")
        flash(_("Reminder deleted."), "success")
    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback(f"Error deleting reminder ID={reminder_id}", e)
        flash(_("Failed to delete reminder."), "danger")

    return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View: Assign Destinations (Apprise, Webhook, SMTP)
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/destinations/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def assign_destinations(reminder_id):
    """
    Assign destinations (Apprise, Webhook, SMTP) to a reminder.

    This view handles the assignment of notification destinations to a
    specific reminder for the current user. If the request method is GET,
    it renders a form for selecting from available Apprise URLs, Webhooks,
    and SMTP configurations that are enabled for the user. If the request
    method is POST, it updates the reminder's destinations based on the form
    input and saves the changes to the database.

    Args:
        reminder_id (int): The ID of the reminder to assign destinations to.

    Returns:
        Response: Renders the assignment form on GET request or redirects to
        the reminder index page on successful update.
    """
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
            log_info_message(
                f"User '{current_user.username}' updated destinations for reminder ID={reminder.id}."
            )
            flash(_("Destinations updated."), "success")
            return redirect(url_for("reminders_bp.overview"))

        # Render the appropriate template based on whether it's a full or partial render (HTMX)
        template = (
            "reminders/assign_destinations_partial.html"  # For HTMX requests
            if request.headers.get("HX-Request")
            else "reminders/assign_destinations_full.html"  # Full page render
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
        from app.utils.logging import log_exception_with_traceback

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
    """
    View: Send Test Reminder
    ======================

    This view sends a test reminder to the assigned destinations.

    The reminder ID is passed as a parameter and the reminder is fetched from
    the database. If the reminder is not found or does not belong to the
    current user, a 404 error is raised.

    The view ensures at least one destination is assigned to the reminder.
    If not, it redirects back to the list of reminders with an error message.

    The view then iterates over the assigned destinations and attempts to
    send a test notification to each one. If any of the destinations fail,
    an error message is added to the list of errors.

    If all destinations succeed, a success message is flashed. If any of
    the destinations fail, an error message is flashed.

    :param int reminder_id: The ID of the reminder to send the test reminder for.
    :return: A redirect to the list of reminders.
    :rtype: flask.Response
    """
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
            log_info_message(f"User '{current_user.username}' sent test reminder ID={reminder.id}.")
        else:
            flash(_("Test reminder failed: ") + "; ".join(errors), "danger")
            log_info_message(
                f"User '{current_user.username}' failed test reminder ID={reminder.id}. Errors: {'; '.join(errors)}"
            )

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback(f"Unexpected error in send_test_reminder ID={reminder_id}", e)
        flash(_("Failed to send test reminder."), "danger")

    return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# View Deatils
# ---------------------------------------------------------------------
@bp.route("view/<int:reminder_id>", strict_slashes=False)
@login_required
def view_reminder(reminder_id):
    """
    View: View Reminder
    =================

    This view shows the details of a single reminder.
    It renders the full and partial templates based on the request type.

    :param int reminder_id: The ID of the reminder to view.
    :return: A rendered template of reminders/view_reminder.html or the partial view.
    :rtype: flask.Response
    """
    try:
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None or reminder.user_id != current_user.id:
            abort(404)

        log_info_message(f"User '{current_user.username}' viewed reminder ID={reminder.id}.")

        # If the request is HTMX, render the partial template for the reminder
        template = (
            "reminders/view_reminder_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "reminders/view_reminder_full.html"  # Full view for normal requests
        )

        return render_template(template, reminder=reminder)

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback(f"Error viewing reminder ID={reminder_id}", e)
        flash(_("Failed to load reminder details."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Schedule Reminder
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/schedule/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def schedule_reminder(reminder_id):
    """
    View: Schedule Reminder (HTMX-compatible)
    ======================

    This view handles scheduling a reminder.

    The reminder ID is passed as a parameter and the reminder is fetched from
    the database. If the reminder is not found or does not belong to the
    current user, a 404 error is raised.

    The view presents a form to the user that allows them to set the start
    date, recurrence rule, end date, and maximum occurrences for the reminder.
    If the form is valid, the reminder is updated in the database and the
    user is redirected to the list of reminders.

    If the form is not valid, the user is presented with the form again with
    the errors highlighted.

    :param int reminder_id: The ID of the reminder to schedule.
    :return: A rendered template of reminders/schedule_reminder.html.
    :rtype: flask.Response
    """
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
            log_info_message(
                f"User '{current_user.username}' updated schedule for reminder ID={reminder.id}."
            )
            flash(_("Reminder schedule updated successfully."), "success")

            # If it's an HTMX request, return a 204 response with a trigger to update the reminder list
            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "reminderListChanged"
                return response

            # If it's not an HTMX request, redirect to the overview page
            return redirect(url_for("reminders_bp.overview"))

        # If the form isn't submitted yet, render the schedule form
        template = (
            "reminders/schedule_reminder_partial.html"  # HTMX-compatible partial (for HTMX requests)
            if request.headers.get("HX-Request")
            else "reminders/schedule_reminder_full.html"  # Full page render
        )
        return render_template(template, form=form, reminder=reminder)

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback(f"Error scheduling reminder ID={reminder_id}", e)
        flash(_("Failed to load or save reminder schedule."), "danger")
        return redirect(url_for("reminders_bp.overview"))


# ---------------------------------------------------------------------
# Email association
# ---------------------------------------------------------------------
@bp.route("<int:reminder_id>/email/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def assign_email_to_reminder(reminder_id):
    """
    View: Assign Email to Reminder
    ==============================

    This view allows users to link an email reminder to a specific reminder
    by selecting from available SMTP configurations and email messages.

    The reminder ID is passed as a parameter, and the user is presented
    with a form to select an SMTP configuration and an email message to
    associate with the reminder. The user can also choose not to assign
    any email by selecting 'None'.

    On form submission, both the SMTP configuration and the email message
    must be selected together or not at all. If the form is valid, the
    reminder's email association is updated in the database, and the user
    is redirected to the list of reminders.

    :param int reminder_id: The ID of the reminder to link an email to.
    :return: A rendered template of reminders/assign_email_reminder.html.
    :rtype: flask.Response
    """
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
                log_info_message(
                    f"User '{current_user.username}' updated email association for reminder ID={reminder.id}."
                )
                flash(_("Email reminder settings updated."), "success")

                # Handle HTMX request (without refreshing the sidebar)
                if request.headers.get("HX-Request"):
                    response = make_response("", 204)
                    response.headers["HX-Trigger"] = "reminderListChanged"  # Trigger update
                    return response

                return redirect(url_for("reminders_bp.overview"))

        # Check if the request is HTMX
        template = (
            "reminders/assign_email_reminder_partial.html"  # HTMX-compatible partial (for HTMX requests)
            if request.headers.get("HX-Request")
            else "reminders/assign_email_reminder_full.html"  # Full page render
        )
        return render_template(
            template,
            form=form,
            reminder=reminder,
            smtp_config_map=smtp_config_map,
            email_messages_map=email_messages_map,
        )
    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

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

    The array is filtered by the current user ID, and the response is
    JSON-formatted.

    :return: A JSON array of reminder objects, each containing a reminder ID
             and whether the reminder is enabled.
    :rtype: flask.Response
    """
    try:
        reminders = Reminder.query.filter_by(user_id=current_user.id).all()
        log_info_message(f"User '{current_user.username}' requested reminder status JSON.")
        return jsonify([{"id": r.id, "is_enabled": r.is_enabled} for r in reminders])
    except Exception as e:
        from app.utils.logging import log_exception_with_traceback

        log_exception_with_traceback("Error retrieving reminder status JSON", e)
        return jsonify({"error": "Failed to retrieve reminder status."}), 500
