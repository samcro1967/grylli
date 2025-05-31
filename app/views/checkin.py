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

from app.models import Message, EmailMessage, db

bp = Blueprint("checkin", __name__)


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
        print("❌ Missing required query parameters")
        flash(_("Invalid check-in link."), "danger")
        return redirect(url_for("index.index"))

    if current_user.id != user_id:
        print("🚫 Unauthorized user")
        flash(_("You are not authorized to check in for this item."), "danger")
        return redirect(url_for("index.index"))

    now = datetime.utcnow()

    if message_type == "message":
        record = Message.query.filter_by(id=message_id, user_id=current_user.id).first()
        if not record:
            abort(404)
        record.last_checkin = now
        record.reminder_sent_at = None  # ✅ reset reminder tracking
        db.session.commit()
        return render_template("checkin/thank_you.html", label=record.label)

    elif message_type == "email":
        record = EmailMessage.query.filter_by(id=message_id, user_id=current_user.id).first()
        if not record:
            abort(404)
        record.last_checkin = now
        record.reminder_sent_at = None  # ✅ reset reminder tracking
        db.session.commit()
        return render_template("checkin/thank_you.html", label=record.label)

    else:
        flash(_("Unsupported check-in type."), "danger")
        return redirect(url_for("index.index"))


@bp.route("/checkin/toggle/<string:type>/<int:id>", methods=["POST"])
@login_required
def toggle_enabled(type, id):
    """
    Toggles a notification or secure email on/off.

    The check-in timer is started when the notification is enabled.
    If the notification is already enabled, this endpoint will disable it.
    If the notification has no schedule or destination, a warning is flashed.

    :param type: The type of record to toggle (message or email)
    :param id: The ID of the record to toggle
    :return: A redirect to the referring page or the index page
    """
    if type == "message":
        record = Message.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        has_dest = record.apprise_destinations or record.webhooks
    elif type == "email":
        record = EmailMessage.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        has_dest = len(record.smtp_configs) > 0  # Ensure SMTP config is assigned for email
    else:
        abort(400)

    # Safely handle None values for checkin_interval_minutes and grace_period_minutes
    has_schedule = (record.checkin_interval_minutes or 0) > 0 and (
        record.grace_period_minutes or 0
    ) > 0

    if has_schedule and has_dest:
        if not record.is_enabled:
            record.is_enabled = True
            record.executed_at = None  # ✅ allow re-execution
            record.reminder_sent_at = None  # ✅ allow re-sending check-in reminder
            if not record.last_checkin:
                record.last_checkin = datetime.utcnow()
            flash(_("✅ Enabled and timer started."), "success")
        else:
            record.is_enabled = False
            flash(_("⛔ Disabled."), "info")
    else:
        flash(_("⚠️ Cannot toggle — missing schedule or destination."), "warning")

    db.session.commit()
    return redirect(request.referrer or url_for("index.index"))
