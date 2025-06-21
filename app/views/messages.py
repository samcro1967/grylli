"""
# ---------------------------------------------------------------------
# messages.py
# app/views/messages.py
# Routes for managing user messages (create, edit, list).
# ---------------------------------------------------------------------
"""

import subprocess
from datetime import timedelta

import requests
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
from app.forms.message_form import MessageForm, ScheduleForm
from app.models import AppriseURL, Message, Webhook
from app.utils.logging import log_info_message

bp = Blueprint("messages_bp", __name__)


class DummyForm(FlaskForm):
    pass


# ---------------------------------------------------------------------
# View: List Messages
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Display a list of messages for the current user.

    Retrieves all messages associated with the logged-in user, ordered
    by creation date in descending order, and renders them in the
    'list_messages.html' template.

    Returns:
        Response: The rendered template displaying the user's messages.
    """

    messages = (
        db.session.query(Message)
        .filter_by(user_id=current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )
    log_info_message(f"User '{current_user.username}' viewed their message list.")
    return render_template("messages/list_messages.html", messages=messages)


# ---------------------------------------------------------------------
# View: Create Message
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# View: Create Message
# ---------------------------------------------------------------------
@bp.route("/create/", methods=["GET", "POST"])
@login_required
def create_message():
    """
    Handle the creation of a new message for the current user.

    Displays a form for creating a new message. If the form is submitted
    and validated, a new Message object is created and saved to the
    database. On successful creation, a success message is flashed, and
    the user is redirected to the message index page.

    Returns:
        Response: The rendered template displaying the message creation form
        or a redirect response on successful message creation.
    """
    form = MessageForm()
    if form.validate_on_submit():
        try:
            message = Message(
                user_id=current_user.id,
                label=form.label.data.strip(),
                subject=form.subject.data.strip(),
                content=form.content.data.strip(),
            )
            db.session.add(message)
            db.session.commit()
            log_info_message(f"User '{current_user.username}' created message ID={message.id}.")
            flash(_("Message created successfully."), "success")
            return redirect(url_for("messages_bp.index"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("create_message failed", e)
            flash(_("An error occurred while creating the message."), "danger")

    return render_template("messages/create_message.html", form=form)


# ---------------------------------------------------------------------
# View: Edit Message
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# View: Edit Message
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/edit/", methods=["GET", "POST"])
@login_required
def edit_message(message_id):
    """
    Handle the editing of an existing message for the current user.

    Retrieves a message identified by the message_id parameter,
    and displays a form for editing the message. If the form is
    submitted and validated, the message is updated and saved to
    the database. On successful update, a success message is flashed,
    and the user is redirected to the message index page.

    Returns:
        Response: The rendered template displaying the message edit form
        or a redirect response on successful message update.
    """
    try:
        message = db.session.get(Message, message_id)
        if message is None or message.user_id != current_user.id:
            abort(404)

        form = MessageForm(obj=message)
        if form.validate_on_submit():
            message.subject = form.subject.data.strip()
            message.content = form.content.data.strip()
            message.label = form.label.data.strip()
            db.session.commit()
            log_info_message(f"User '{current_user.username}' updated message ID={message.id}.")
            flash(_("Message updated successfully."), "success")
            return redirect(url_for("messages_bp.index"))

        return render_template("messages/edit_message.html", form=form, message=message)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("edit_message failed", e)
        flash(_("An error occurred while updating the message."), "danger")
        return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# View: Delete Message
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/delete/", methods=["POST"])
@login_required
def delete_message(message_id):
    """
    Handle the deletion of an existing message for the current user.

    Retrieves a message identified by the message_id parameter,
    and deletes it from the database if it belongs to the current user.
    On successful deletion, a success message is flashed, and the user
    is redirected to the message index page.

    Args:
        message_id (int): The ID of the message to be deleted.

    Returns:
        Response: A redirect response to the message index page.
    """
    try:
        message = db.session.get(Message, message_id)
        if message is None or message.user_id != current_user.id:
            abort(404)

        db.session.delete(message)
        db.session.commit()
        log_info_message(f"User '{current_user.username}' deleted message ID={message_id}.")
        flash(_("Message deleted."), "success")

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("delete_message failed", e)
        flash(_("An error occurred while deleting the message."), "danger")

    return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# View: Assign Destinations (Apprise + Webhooks)
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/destinations/", methods=["GET", "POST"])
@login_required
def assign_destinations(message_id):
    """
    Assign destinations (Apprise URLs and Webhooks) to a message.

    This view handles the assignment of notification destinations to a
    specific message for the current user. If the request method is GET,
    it renders a form for selecting from available Apprise URLs and Webhooks
    that are enabled for the user. If the request method is POST, it updates
    the message's destinations based on the form input and saves the changes
    to the database.

    Args:
        message_id (int): The ID of the message to assign destinations to.

    Returns:
        Response: Renders the assignment form on GET request or redirects to
        the message index page on successful update.
    """
    try:
        message = db.session.get(Message, message_id)
        if message is None or message.user_id != current_user.id:
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

        if request.method == "POST" and form.validate_on_submit():
            selected_apprise_ids = request.form.getlist("apprise_destinations")
            selected_webhook_ids = request.form.getlist("webhooks")

            message.apprise_destinations = [
                a for a in apprise_options if str(a.id) in selected_apprise_ids
            ]
            message.webhooks = [w for w in webhook_options if str(w.id) in selected_webhook_ids]

            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' updated destinations for message ID={message_id}."
            )
            flash(_("Destinations updated."), "success")
            return redirect(url_for("messages_bp.index"))

        return render_template(
            "messages/assign_destinations.html",
            form=form,
            message=message,
            apprise_options=apprise_options,
            webhook_options=webhook_options,
        )
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("assign_destinations failed", e)
        flash(_("An error occurred while assigning destinations."), "danger")
        return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# View: Assign Schedule
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/schedule", methods=["GET", "POST"])
@login_required
def schedule_message(message_id):
    """
    Handle the scheduling of an existing message for the current user.

    This view handles the display and submission of a form for updating
    the schedule of a message for the current user. If the request method
    is GET, it renders the form for setting the checkin interval and
    grace period. If the request method is POST and the form is valid,
    the message is updated with the new schedule, and the user is
    redirected to the message index page.

    Args:
        message_id (int): The ID of the message to be updated.

    Returns:
        Response: A rendered template displaying the schedule form on GET
        request or a redirect response on successful update.
    """
    try:
        message = db.session.get(Message, message_id)
        if not message or message.user_id != current_user.id:
            abort(404)

        form = ScheduleForm(obj=message)

        # Only set defaults on GET (not POST where user input takes precedence)
        if request.method == "GET":
            # Convert checkin minutes back into compound fields
            remaining = (message.checkin_interval_minutes or 0) * 60
            form.checkin_years.data = remaining // (365 * 24 * 3600)
            remaining %= 365 * 24 * 3600
            form.checkin_months.data = remaining // (30 * 24 * 3600)
            remaining %= 30 * 24 * 3600
            form.checkin_weeks.data = remaining // (7 * 24 * 3600)
            remaining %= 7 * 24 * 3600
            form.checkin_days.data = remaining // (24 * 3600)
            remaining %= 24 * 3600
            form.checkin_hours.data = remaining // 3600
            remaining %= 3600
            form.checkin_minutes.data = remaining // 60

            # Convert grace period
            remaining = (message.grace_period_minutes or 0) * 60
            form.grace_years.data = remaining // (365 * 24 * 3600)
            remaining %= 365 * 24 * 3600
            form.grace_months.data = remaining // (30 * 24 * 3600)
            remaining %= 30 * 24 * 3600
            form.grace_weeks.data = remaining // (7 * 24 * 3600)
            remaining %= 7 * 24 * 3600
            form.grace_days.data = remaining // (24 * 3600)
            remaining %= 24 * 3600
            form.grace_hours.data = remaining // 3600
            remaining %= 3600
            form.grace_minutes.data = remaining // 60

        if form.validate_on_submit():
            checkin_seconds = compute_total_seconds(form, "checkin")
            grace_seconds = compute_total_seconds(form, "grace")

            message.checkin_interval_minutes = checkin_seconds // 60
            message.grace_period_minutes = grace_seconds // 60

            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' updated schedule for message ID={message_id}."
            )
            flash(_("Schedule updated successfully."), "success")
            return redirect(url_for("messages_bp.index"))

        return render_template(
            "messages/schedule_message.html", form=form, message=message, config=current_app.config
        )
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("schedule_message failed", e)
        flash(_("An error occurred while updating the schedule."), "danger")
        return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# Messagaes Summary
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/view", methods=["GET"])
@login_required
def view_message(message_id):
    """
    Displays a summary of a message.

    Args:
        message_id (int): The ID of the message to be viewed.

    Returns:
        Response: A rendered template displaying the message summary.
    """
    try:
        message = Message.query.get_or_404(message_id)
        if message.user_id != current_user.id:
            flash(_("Access denied."), "danger")
            log_info_message(f"Unauthorized access attempt to message ID={message_id}")
            return redirect(url_for("messages_bp.index"))

        checkin_human = format_minutes_as_duration(message.checkin_interval_minutes)
        grace_human = format_minutes_as_duration(message.grace_period_minutes)

        log_info_message(f"User '{current_user.username}' viewed message ID={message_id}.")

        return render_template(
            "messages/view_message.html",
            message=message,
            checkin_human=checkin_human,
            grace_human=grace_human,
        )
    except Exception as e:
        log_exception_with_traceback("view_message failed", e)
        flash(_("An error occurred while loading the message."), "danger")
        return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# Compute the total number of seconds
# ---------------------------------------------------------------------
def compute_total_seconds(form, prefix):
    """
    Computes the total number of seconds represented by a set of form fields.

    The fields are expected to be named "<prefix>_years", "<prefix>_months",
    "<prefix>_weeks", "<prefix>_days", "<prefix>_hours", and "<prefix>_minutes",
    and "<prefix>_seconds" if applicable.

    Args:
        form (FlaskForm): The form containing the fields.
        prefix (str): The prefix to use when looking up the fields.

    Returns:
        int: The total number of seconds.
    """
    return (
        (form[f"{prefix}_years"].data or 0) * 365 * 24 * 3600
        + (form[f"{prefix}_months"].data or 0) * 30 * 24 * 3600
        + (form[f"{prefix}_weeks"].data or 0) * 7 * 24 * 3600
        + (form[f"{prefix}_days"].data or 0) * 24 * 3600
        + (form[f"{prefix}_hours"].data or 0) * 3600
        + (form[f"{prefix}_minutes"].data or 0) * 60
    )
    if hasattr(form, f"{prefix}_seconds"):
        total += getattr(form, f"{prefix}_seconds").data or 0
    return total


# ---------------------------------------------------------------------
# Format minutes as duration
# ---------------------------------------------------------------------
def format_minutes_as_duration(minutes):
    """
    Format a duration given in minutes as a human-readable string.

    Args:
        minutes (int): The duration in minutes.

    Returns:
        str: A human-readable string representation of the duration.
    """
    seconds = (minutes or 0) * 60
    parts = []
    units = [
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("week", 7 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
    ]
    for label, unit_seconds in units:
        value, seconds = divmod(seconds, unit_seconds)
        if value:
            parts.append(f"{value} {label}{'s' if value != 1 else ''}")
    return ", ".join(parts) if parts else "0 minutes"


# ---------------------------------------------------------------------
# Messages Status
# ---------------------------------------------------------------------
@bp.route("/status", methods=["GET"])
@login_required
def message_status():
    """
    API endpoint to return the list of messages and their current enabled status
    for the logged-in user. Used for UI polling to refresh enabled/disabled states.
    """
    try:
        messages = Message.query.filter_by(user_id=current_user.id).all()
        status_list = [{"id": msg.id, "is_enabled": msg.is_enabled} for msg in messages]
        return jsonify(status_list)
    except Exception as e:
        log_exception_with_traceback("message_status polling failed", e)
        return jsonify({"error": _("Unable to fetch message status.")}), 500


# ---------------------------------------------------------------------
# Message Test
# ---------------------------------------------------------------------
@bp.route("/<int:message_id>/send-test", methods=["POST"])
@login_required
def send_test_message(message_id):
    """
    Sends a test message for the specified user message via Apprise and Webhooks.

    Args:
        message_id (int): The ID of the message to test.

    Returns:
        Response: A redirect to the index page with flash feedback.
    """
    message = Message.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()

    if not message.apprise_destinations and not message.webhooks:
        flash(_("No destinations assigned to this message."), "danger")
        log_info_message(
            f"User '{current_user.username}' attempted to send test message ID={message_id} without destinations."
        )
        return redirect(url_for("messages_bp.view_message", message_id=message.id))

    success, errors = _send_test_via_apprise_and_webhooks(message)

    if success:
        log_info_message(
            f"User '{current_user.username}' sent test message for ID={message_id}. Success={success}. Errors={errors}"
        )
        flash(_("Test message sent successfully."), "success")
    else:
        flash(_("Test message failed: ") + "; ".join(errors), "danger")
        log_info_message(
            f"User '{current_user.username}' failed to send test message ID={message_id}: {'; '.join(errors)}"
        )

    return redirect(url_for("messages_bp.index"))


# ---------------------------------------------------------------------
# Notification Test
# ---------------------------------------------------------------------
def _send_test_via_apprise_and_webhooks(message):
    """
    Sends a test message to all Apprise and Webhook destinations.

    Args:
        message (Message): The message instance to test.

    Returns:
        tuple: (success: bool, errors: list of str)
    """
    success = True
    errors = []

    # Apprise Destinations
    for apprise in message.apprise_destinations:
        cmd = [
            "apprise",
            "--title",
            message.subject or "Notification",
            "--body",
            message.content,
            apprise.url.strip(),
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True, text=True)
            log_info_message(
                f"Apprise test sent for message ID={message.id} via '{apprise.label}'."
            )
        except subprocess.CalledProcessError as exc:
            success = False
            error_msg = exc.stderr or exc.stdout or "Unknown error"
            errors.append(f"Apprise ({apprise.label}): {error_msg}")
            log_info_message(f"Apprise test failed for '{apprise.label}': {error_msg}")

    # Webhook Destinations
    for hook in message.webhooks:
        try:
            response = requests.post(
                hook.endpoint.strip(),
                json={"subject": message.subject, "content": message.content},
                timeout=10,
            )

            if response.status_code >= 400:
                success = False
                error_detail = f"{response.status_code} {response.text}"
                errors.append(f"Webhook ({hook.label}): {error_detail}")
                log_info_message(f"Webhook test failed for '{hook.label}': {error_detail}")
            else:
                log_info_message(
                    f"Webhook test sent for message ID={message.id} via '{hook.label}'."
                )
        except requests.RequestException as exc:
            success = False
            errors.append(f"Webhook ({hook.label}): {str(exc)}")
            log_info_message(f"Webhook test raised exception for '{hook.label}': {exc}")

    return success, errors
