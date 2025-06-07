"""
# ---------------------------------------------------------------------
# checkin.py
# app/views/checkin.py
# Blueprint for user check-in and enable/disable routes.
# ---------------------------------------------------------------------
"""

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.models import EmailMessage, Message, db
from app.utils.logging import log_info_message

bp = Blueprint("checkin", __name__)


# ---------------------------------------------------------------------
# User check in route
# ---------------------------------------------------------------------
@bp.route("/checkin", strict_slashes=False)
@login_required
def handle_checkin():
    """
    Entry point for user check-in.
    URL format: /checkin?type=message&id=123&user=4
    """

    message_type = request.args.get("type")
    message_id = request.args.get("id", type=int)
    try:
        user_id = int(request.args.get("user", ""))
    except (ValueError, TypeError):
        user_id = None

    if not all([message_type, message_id, user_id]):
        log_info_message(f"Check-in failed — missing or invalid parameters.")
        flash(_("Invalid check-in link."), "danger")
        return redirect(url_for("index.index"))

    if current_user.id != user_id:
        log_info_message(
            f"User '{current_user.username}' attempted to check in for user ID={user_id} — denied."
        )
        flash(_("You are not authorized to check in for this item."), "danger")
        return redirect(url_for("index.index"))

    now = datetime.utcnow()

    # Lookup record based on type
    if message_type == "message":
        record = Message.query.filter_by(id=message_id, user_id=current_user.id).first()
    elif message_type == "email":
        record = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first()
    else:
        log_info_message(
            f"User '{current_user.username}' attempted check-in with unsupported type: '{message_type}'"
        )
        flash(_("Unsupported check-in type."), "danger")
        return redirect(url_for("index.index"))

    if not record:
        abort(404)

    # --- SCENARIO LOGIC STARTS HERE ---
    if not record.is_enabled:
        if record.executed_at is not None:
            # Scenario 3: Already executed and now disabled
            return render_template("checkin/executed_disabled.html", label=record.label)
        else:
            # Scenario 4: Currently disabled (never executed)
            return render_template("checkin/disabled.html", label=record.label)
    elif record.reminder_sent_at is None:
        # Scenario 2: Already checked in for this cycle
        return render_template("checkin/already_checked_in.html", label=record.label)
    else:
        # Scenario 1: Valid check-in
        record.last_checkin = now
        record.reminder_sent_at = None  # Mark as checked in
        db.session.commit()
        log_info_message(
            f"User '{current_user.username}' checked in for {message_type} ID={message_id}."
        )
        return render_template("checkin/thank_you.html", label=record.label)


# ---------------------------------------------------------------------
# Check in enable/disable toggle route
# ---------------------------------------------------------------------
@bp.route("/checkin/toggle/<string:type>/<int:id>", methods=["POST"])
@login_required
def toggle_enabled(type, id):
    """
    Toggles a notification, email, or reminder on/off.

    Checks schedules, destinations, and for reminders specifically, prevents enabling if the start date/time is in the past.

    :param type: The type of record to toggle (message, email, reminder)
    :param id: The ID of the record to toggle
    :return: A redirect to the referring page or the index page
    """
    if type == "message":
        record = Message.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        has_dest = record.apprise_destinations or record.webhooks
        has_schedule = (record.checkin_interval_minutes or 0) > 0 and (
            record.grace_period_minutes or 0
        ) > 0

    elif type == "email":
        record = EmailMessage.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        has_dest = len(record.smtp_configs) > 0
        has_schedule = (record.checkin_interval_minutes or 0) > 0 and (
            record.grace_period_minutes or 0
        ) > 0

    elif type == "reminder":
        from app.models import Reminder  # Ensure Reminder is imported

        record = Reminder.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        has_schedule = record.start_at is not None
        has_dest = (
            (record.apprise_destinations and len(record.apprise_destinations) > 0)
            or (record.webhooks and len(record.webhooks) > 0)
            or (record.smtp_configs and len(record.smtp_configs) > 0)
        )
    else:
        abort(400)

    if has_schedule and has_dest:
        if not record.is_enabled:
            if type == "reminder":
                now = datetime.now()
                if record.start_at and record.start_at <= now:
                    flash(_("⚠️ Cannot enable reminder: Start date/time is in the past."), "danger")
                    log_info_message(
                        f"User '{current_user.username}' attempted to enable reminder ID={id}, but start_at is in the past."
                    )
                    return redirect(request.referrer or url_for("index.index"))

            record.is_enabled = True

            # 🆕 Reset one-time reminders when re-enabled
            if type == "reminder" and not record.recurrence_rule:
                record.last_sent_at = None
                record.occurrences_sent = 0

            if hasattr(record, "executed_at"):
                record.executed_at = None
            if hasattr(record, "reminder_sent_at"):
                record.reminder_sent_at = None
            if hasattr(record, "last_checkin") and not record.last_checkin:
                record.last_checkin = datetime.utcnow()

            log_info_message(f"User '{current_user.username}' enabled {type} ID={id}.")
            flash(_("✅ Enabled and timer started."), "success")
        else:
            record.is_enabled = False
            if type == "reminder":
                record.recurrence_rule = None
                record.end_at = None
                record.max_occurrences = None
                record.last_sent_at = None
                record.occurrences_sent = 0
            log_info_message(f"User '{current_user.username}' disabled {type} ID={id}.")
            flash(_("⛔ Disabled."), "info")
    else:
        flash(_("⚠️ Cannot toggle — missing schedule or destination."), "warning")
        log_info_message(
            f"User '{current_user.username}' attempted to toggle {type} ID={id}, but missing schedule or destination."
        )

    db.session.commit()
    return redirect(request.referrer or url_for("index.index"))
