# ---------------------------------------------------------------------
# checkin.py
# app/views/checkin.py
# Blueprint for user check-in and enable/disable routes.
# ---------------------------------------------------------------------

from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.models import EmailMessage, Message, db
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.utils.security import get_safe_redirect

bp = Blueprint("checkin", __name__)


# ---------------------------------------------------------------------
# User check in route
# ---------------------------------------------------------------------
@bp.route("checkin", strict_slashes=False)
@login_required
def handle_checkin():
    """
    Entry point for user check-in.
    URL format: /checkin?type=message&id=123&user=4
    """
    try:
        message_type = request.args.get("type")
        message_id = request.args.get("id", type=int)
        try:
            user_id = int(request.args.get("user", ""))
        except (ValueError, TypeError):
            user_id = None

        if not all([message_type, message_id, user_id]):
            log_info_message(
                f"User '{current_user.username}' — Check-in failed (missing/invalid parameters)"
            )
            flash(_("Invalid check-in link."), "danger")
            return redirect(url_for("home.index"))

        if current_user.id != user_id:
            log_info_message(
                f"User '{current_user.username}' attempted to check in for user ID={user_id} — denied."
            )
            flash(_("You are not authorized to check in for this item."), "danger")
            return redirect(url_for("home.index"))

        now = datetime.now(timezone.utc)

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
            return redirect(url_for("home.index"))

        if not record:
            log_info_message(
                f"User '{current_user.username}' attempted check-in on non-existent {message_type} ID={message_id}"
            )
            abort(404)

        # --- SCENARIO LOGIC STARTS HERE ---
        if not record.is_enabled:
            if record.executed_at is not None:
                return render_template("checkin/executed_disabled.html", label=record.label)
            else:
                return render_template("checkin/disabled.html", label=record.label)

        # Determine if check-in came from UI vs. email
        from_ui = request.referrer and "/overview/schedule/" in request.referrer

        # Handle "already checked in" case — but allow UI override
        if record.reminder_sent_at is None and not from_ui:
            return render_template("checkin/already_checked_in.html", label=record.label)

        # Proceed with check-in
        record.last_checkin = now
        record.reminder_sent_at = None
        db.session.commit()

        log_info_message(
            f"CheckIn - {current_user.username} - {message_type} | ID={message_id}, label={record.label}, from_ui={from_ui}"
        )
        return render_template("checkin/thank_you.html", label=record.label)

    except Exception as e:
        log_exception_with_traceback("Unhandled error in handle_checkin()", e)
        flash(_("An error occurred during check-in."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Check in enable/disable toggle route
# ---------------------------------------------------------------------
@bp.route("checkin/toggle/<string:type>/<int:id>", methods=["POST"], strict_slashes=False)
@login_required
def toggle_enabled(type, id):
    """
    Toggles a notification, email, or reminder on/off.
    """
    try:
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
            from app.models import Reminder

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
                        flash(
                            _("⚠️ Cannot enable reminder: Start date/time is in the past."), "danger"
                        )
                        log_info_message(
                            f"User '{current_user.username}' attempted to enable reminder ID={id}, but start_at is in the past."
                        )
                        return redirect(
                            # Safe redirect: `request.referrer` is sanitized to ensure same-origin only
                            get_safe_redirect(request.referrer, fallback_endpoint="home.index")
                        )

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

    except Exception as e:
        log_exception_with_traceback(f"Unhandled error in toggle_enabled({type}, {id})", e)
        flash(_("An error occurred while toggling status."), "danger")

    # Safe redirect: `request.referrer` is sanitized to ensure same-origin only
    return redirect(get_safe_redirect(request.referrer, fallback_endpoint="home.index"))
