# ---------------------------------------------------------------------
# reminders.py
# app/views/reminders.py
# Routes for managing user reminders (create, edit, list, delete, destinations).
# ---------------------------------------------------------------------

import os
import subprocess
from datetime import datetime

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
from app.utils.logging import log_info_message

bp = Blueprint("reminders_bp", __name__)


class DummyForm(FlaskForm):
    pass


# ---------------------------------------------------------------------
# View: List Reminders
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET"])
@login_required
def index():
    """
    View: List Reminders
    ===================

    This view renders a table and a card view of all reminders for the current user.
    The table view displays the reminder label, subject, content, and next occurrence.
    The card view displays the reminder label, subject, content, next occurrence, and
    the assigned destinations (Apprise URLs, Webhooks, and Email settings).

    :param None:
    :return: A rendered template of reminders/list_reminders.html.
    :rtype: flask.Response
    """
    reminders = (
        db.session.query(Reminder)
        .filter_by(user_id=current_user.id)
        .order_by(Reminder.created_at.desc())
        .all()
    )
    now = datetime.now()
    log_info_message(f"User '{current_user.username}' viewed their reminders list.")
    return render_template("reminders/list_reminders.html", reminders=reminders, now=now)


# ---------------------------------------------------------------------
# View: Create Reminder
# ---------------------------------------------------------------------
@bp.route("/create/", methods=["GET", "POST"])
@login_required
def create_reminder():
    """
    View: Create Reminder
    ===================

    This view handles the creation of new reminders.

    The user is presented with a form to enter the reminder label, subject,
    and content. The reminder is then created with the user ID of the current
    user and the provided form data. The reminder is then added to the
    database and the user is redirected to the list of reminders.

    :param None:
    :return: A rendered template of reminders/create_reminder.html.
    :rtype: flask.Response
    """
    form = ReminderForm()
    if form.validate_on_submit():
        reminder = Reminder(
            user_id=current_user.id,
            label=form.label.data.strip(),
            subject=form.subject.data.strip(),
            content=form.content.data.strip(),
            is_enabled=True,  # default to enabled or set your default accordingly
        )
        db.session.add(reminder)
        db.session.commit()
        log_info_message(
            f"User '{current_user.username}' created reminder '{reminder.label}' (ID={reminder.id})."
        )
        flash(_("Reminder created successfully."), "success")
        return redirect(url_for("reminders_bp.index"))
    return render_template("reminders/create_reminder.html", form=form)


# ---------------------------------------------------------------------
# View: Edit Reminder
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/edit/", methods=["GET", "POST"])
@login_required
def edit_reminder(reminder_id):
    """
    View: Edit Reminder
    =================

    This view handles editing an existing reminder.

    The reminder ID is passed as a parameter and the user is presented with a
    form that is pre-filled with the reminder data. The user can then edit the
    form and submit it to update the reminder. If the form is valid, the
    reminder is updated in the database and the user is redirected to the
    list of reminders.

    :param int reminder_id: The ID of the reminder to edit.
    :return: A rendered template of reminders/edit_reminder.html.
    :rtype: flask.Response
    """
    reminder = db.session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != current_user.id:
        abort(404)
    form = ReminderForm(obj=reminder)
    if form.validate_on_submit():
        reminder.label = form.label.data.strip()
        reminder.subject = form.subject.data.strip()
        reminder.content = form.content.data.strip()
        db.session.commit()
        log_info_message(f"User '{current_user.username}' edited reminder ID={reminder.id}.")
        flash(_("Reminder updated successfully."), "success")
        return redirect(url_for("reminders_bp.index"))
    return render_template("reminders/edit_reminder.html", form=form, reminder=reminder)


# ---------------------------------------------------------------------
# View: Delete Reminder
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/delete/", methods=["POST"])
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
    reminder = db.session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != current_user.id:
        abort(404)
    db.session.delete(reminder)
    db.session.commit()
    log_info_message(f"User '{current_user.username}' deleted reminder ID={reminder.id}.")
    flash(_("Reminder deleted."), "success")
    return redirect(url_for("reminders_bp.index"))


# ---------------------------------------------------------------------
# View: Assign Destinations (Apprise, Webhook, SMTP)
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/destinations/", methods=["GET", "POST"])
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
        Webhook.query.filter_by(user_id=current_user.id, enabled=True).order_by(Webhook.label).all()
    )
    smtp_options = (
        UserMailSettings.query.filter_by(user_id=current_user.id, enabled=True)
        .order_by(UserMailSettings.label)
        .all()
    )

    if request.method == "POST" and form.validate_on_submit():
        selected_apprise_ids = request.form.getlist("apprise_destinations")
        selected_webhook_ids = request.form.getlist("webhooks")
        selected_smtp_id = request.form.get("smtp_config")  # <--- Only one value (radio)

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
        return redirect(url_for("reminders_bp.index"))

    return render_template(
        "reminders/assign_destinations.html",
        form=form,
        reminder=reminder,
        apprise_options=apprise_options,
        webhook_options=webhook_options,
        smtp_options=smtp_options,
    )


# ---------------------------------------------------------------------
# Test Reminder
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/send-test", methods=["POST"])
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
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()

    # Ensure at least one destination assigned
    if not (reminder.apprise_destinations or reminder.webhooks or reminder.smtp_configs):
        flash(_("No destinations assigned to this reminder."), "danger")
        return redirect(url_for("reminders_bp.index"))

    success = True
    errors = []
    # --- Apprise ---
    for apprise in reminder.apprise_destinations:
        ok, msg = send_test_apprise_notification(apprise.url)
        if not ok:
            errors.append(f"Apprise ({apprise.label}): {msg}")
            success = False

    # --- Webhook ---
    for webhook in reminder.webhooks:
        ok, msg = send_test_webhook_notification(webhook.endpoint)
        if not ok:
            errors.append(f"Webhook ({webhook.label}): {msg}")
            success = False

    # --- SMTP ---
    for smtp in reminder.smtp_configs:
        try:
            email_msg = reminder.email_messages[0] if reminder.email_messages else None
            if not email_msg:
                raise Exception(_("No email message linked to this reminder."))

            if not smtp.enabled:
                raise Exception(_("SMTP configuration is disabled."))

            # Password already decrypted via property
            decrypted_password = smtp.smtp_password

            # Build Apprise mailto URL
            apprise_url = (
                f"mailtos://{current_user.email}"
                f"?smtp={smtp.smtp_host}"
                f"&user={smtp.smtp_username}"
                f"&pass={decrypted_password}"
                f"&secure=starttls"
            )

            # Construct Apprise CLI command
            cmd = [
                "apprise",
                "--title",
                "[TEST] " + email_msg.subject,
                "--body",
                email_msg.body,
            ]

            # Attach files
            for f in email_msg.files:
                cmd += ["--attach", os.path.join("uploads", f.file_path)]

            cmd.append(apprise_url)

            result = subprocess.run(cmd, capture_output=True, check=True, text=True)

        except subprocess.CalledProcessError as e:
            errors.append(f"SMTP ({smtp.label}): {e.stderr or e.stdout or 'Unknown error'}")
            success = False
        except Exception as e:
            errors.append(f"SMTP ({smtp.label}): {str(e)}")
            success = False

        if success:
            flash(_("Test reminder sent successfully."), "success")
            log_info_message(f"User '{current_user.username}' sent test reminder ID={reminder.id}.")
        else:
            flash(_("Test reminder failed: ") + "; ".join(errors), "danger")
            log_info_message(
                f"User '{current_user.username}' failed test reminder ID={reminder.id}. Errors: {'; '.join(errors)}"
            )

    return redirect(url_for("reminders_bp.index"))


# ---------------------------------------------------------------------
# View Deatils
# ---------------------------------------------------------------------
@bp.route("/view/<int:reminder_id>")
@login_required
def view_reminder(reminder_id):
    """
    View: View Reminder
    =================

    This view shows the details of a single reminder.

    :param int reminder_id: The ID of the reminder to view.
    :return: A rendered template of reminders/view_reminder.html.
    :rtype: flask.Response
    """
    from app.models import Reminder  # adjust if needed

    reminder = Reminder.query.get_or_404(reminder_id)
    log_info_message(f"User '{current_user.username}' viewed reminder ID={reminder.id}.")
    return render_template("reminders/view_reminder.html", reminder=reminder)


# ---------------------------------------------------------------------
# Schedule Reminder
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/schedule/", methods=["GET", "POST"])
@login_required
def schedule_reminder(reminder_id):
    """
    View: Schedule Reminder
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
        return redirect(url_for("reminders_bp.index"))

    elif request.method == "POST":
        flash(_("Please correct the errors below."), "danger")
        log_info_message(
            f"User '{current_user.username}' submitted an invalid reminder schedule form for reminder ID={reminder.id}."
        )

    return render_template("reminders/schedule_reminder.html", form=form, reminder=reminder)


# ---------------------------------------------------------------------
# Email association
# ---------------------------------------------------------------------
@bp.route("/<int:reminder_id>/email/", methods=["GET", "POST"])
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

    reminder = db.session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != current_user.id:
        abort(404)

    form = EmailReminderLinkForm()

    # Fetch data
    smtp_configs = UserMailSettings.query.filter_by(user_id=current_user.id, enabled=True).all()
    email_messages = EmailMessage.query.filter_by(user_id=current_user.id).all()

    # Add 'None' option to allow unassignment
    form.smtp_config.choices = [("none", _("None"))] + [(str(s.id), s.label) for s in smtp_configs]
    form.message.choices = [("none", _("None"))] + [(str(m.id), m.label) for m in email_messages]

    # Maps for label display
    smtp_config_map = {str(s.id): s for s in smtp_configs}
    email_messages_map = {str(m.id): m for m in email_messages}

    # Preselect current values on GET
    if request.method == "GET":
        if reminder.smtp_configs:
            form.smtp_config.data = str(reminder.smtp_configs[0].id)
        else:
            form.smtp_config.data = "none"

        if reminder.email_messages:
            form.message.data = str(reminder.email_messages[0].id)
        else:
            form.message.data = "none"

    # Handle submission
    if form.validate_on_submit():
        smtp_selected = form.smtp_config.data != "none"
        msg_selected = form.message.data != "none"

        # Enforce: both or none must be selected
        if smtp_selected != msg_selected:
            flash(
                _("You must select both an SMTP config and an email message, or neither."),
                "warning",
            )
        else:
            # Update SMTP
            reminder.smtp_configs = (
                [s for s in smtp_configs if str(s.id) == form.smtp_config.data]
                if smtp_selected
                else []
            )

            # Update EmailMessage link
            reminder.email_messages = (
                [EmailMessage.query.get(int(form.message.data))] if msg_selected else []
            )

            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' updated email association for reminder ID={reminder.id}."
            )
            flash(_("Email reminder settings updated."), "success")
            return redirect(url_for("reminders_bp.index"))

    return render_template(
        "reminders/assign_email_reminder.html",
        form=form,
        reminder=reminder,
        smtp_config_map=smtp_config_map,
        email_messages_map=email_messages_map,
    )


# ---------------------------------------------------------------------
# Reminder Status
# --------------------------------------------------------------
@bp.route("/status", methods=["GET"])
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
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()
    log_info_message(f"User '{current_user.username}' requested reminder status JSON.")
    return jsonify([{"id": r.id, "is_enabled": r.is_enabled} for r in reminders])
