# ---------------------------------------------------------------------
# scheduler.py
# app/services/scheduler/scheduler.py
# Core scheduling logic to check for reminders and execute actions
# ---------------------------------------------------------------------

import traceback

# ------------------------ Imports (PEP8 order) -----------------------
from datetime import datetime, timedelta, timezone

from dateutil.rrule import rrulestr

from app.extensions import db
from app.models import EmailMessage, Message, Reminder, User, UserMailSettings
from app.services.scheduler.apprise_utils import execute_apprise
from app.services.scheduler.backup_utils import create_backup
from app.services.scheduler.email_utils import (
    send_checkin_email,
    send_owner_notice,
    send_reminder_email,
    send_secure_email,
)
from app.services.scheduler.webhook_utils import execute_webhooks
from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# process_checkins_and_overdue_actions
# ---------------------------------------------------------------------
def process_checkins_and_overdue_actions():
    """
    Main entry point for running all scheduled tasks.
    """
    try:
        find_messages_needing_checkin_reminder()
        log_info_message(
            "Scheduler [ProcessCheckinsAndOverdueActions] - Success - Processed check-ins and overdue actions."
        )
    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [ProcessCheckinsAndOverdueActions] - Failure - Error in check-in reminder processing: {e}\n{traceback.format_exc()}"
        )

    try:
        find_expired_items()
        log_info_message(
            "Scheduler [ProcessCheckinsAndOverdueActions] - Success - Processed expired items."
        )
    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [ProcessCheckinsAndOverdueActions] - Failure - Error in expired item processing: {e}\n{traceback.format_exc()}"
        )


# ---------------------------------------------------------------------
# find_messages_needing_checkin_reminder
# ---------------------------------------------------------------------
def find_messages_needing_checkin_reminder():
    now = datetime.now(timezone.utc)
    messages = Message.query.filter_by(is_enabled=True).all()
    emails = EmailMessage.query.filter_by(is_enabled=True).all()

    for item in messages + emails:
        if item.checkin_interval_minutes is None or item.last_checkin is None:
            continue

        delta = timedelta(minutes=item.checkin_interval_minutes)

        last_checkin = item.last_checkin
        if last_checkin.tzinfo is None:
            last_checkin = last_checkin.replace(tzinfo=timezone.utc)

        if now - last_checkin >= delta:
            if item.reminder_sent_at is None:
                try:
                    user = db.session.get(User, item.user_id)
                    if user:
                        item.reminder_sent_at = now
                        db.session.commit()
                        send_checkin_email(user, item)
                        log_info_message(
                            f"Scheduler [SendCheckinEmail] - Success - Check-in reminder sent to {user.email} for {item.label}"
                        )
                    else:
                        log_error_message(
                            f"ERROR - Scheduler [SendCheckinEmail] - Failure - Cannot send reminder — user {item.user_id} not found"
                        )
                except Exception as e:
                    db.session.rollback()
                    log_error_message(
                        f"ERROR - Scheduler [SendCheckinEmail] - Failure - Error sending reminder for {item.label}: {e}\n{traceback.format_exc()}"
                    )


# ---------------------------------------------------------------------
# find_expired_items
# ---------------------------------------------------------------------
def find_expired_items():
    now = datetime.now(timezone.utc)
    messages = Message.query.filter_by(is_enabled=True).all()
    emails = EmailMessage.query.filter_by(is_enabled=True).all()

    for item in messages:
        if (
            item.executed_at is not None
            or item.grace_period_minutes is None
            or item.last_checkin is None
            or item.reminder_sent_at is None
        ):
            log_info_message(
                f"Scheduler [FindExpiredItems] - Skipping {item.label} — not eligible for expiration"
            )
            continue

        if item.reminder_sent_at.tzinfo is None:
            item.reminder_sent_at = item.reminder_sent_at.replace(tzinfo=timezone.utc)

        if now - item.reminder_sent_at < timedelta(minutes=item.grace_period_minutes):
            log_info_message(
                f"Scheduler [FindExpiredItems] - Skipping {item.label} — grace period not yet elapsed"
            )
            continue

        grace = timedelta(minutes=item.checkin_interval_minutes + item.grace_period_minutes)
        if now - item.last_checkin >= grace:
            try:
                log_info_message(
                    f"Scheduler [ExecuteExpiredMessage] - Success - Executing expired message: {item.label}"
                )
                execute_apprise(item)
                execute_webhooks(item)
                send_owner_notice(item)
                item.executed_at = datetime.now(timezone.utc)
                item.is_enabled = False
                db.session.commit()
                log_info_message(
                    f"Scheduler [ExecuteExpiredMessage] - Success - Executed and disabled message: {item.label}"
                )
            except Exception as e:
                db.session.rollback()
                log_error_message(
                    f"ERROR - Scheduler [ExecuteExpiredMessage] - Failure - Error executing message '{item.label}': {e}\n{traceback.format_exc()}"
                )

    for item in emails:
        if (
            item.executed_at is not None
            or item.grace_period_minutes is None
            or item.last_checkin is None
            or item.reminder_sent_at is None
        ):
            log_info_message(
                f"Scheduler [FindExpiredItems] - Skipping {item.label} — not eligible for expiration"
            )
            continue

        if item.reminder_sent_at.tzinfo is None:
            item.reminder_sent_at = item.reminder_sent_at.replace(tzinfo=timezone.utc)

        if now - item.reminder_sent_at < timedelta(minutes=item.grace_period_minutes):
            log_info_message(
                f"Scheduler [FindExpiredItems] - Skipping {item.label} — grace period not yet elapsed"
            )
            continue

        grace = timedelta(minutes=item.checkin_interval_minutes + item.grace_period_minutes)
        if now - item.last_checkin >= grace:
            try:
                log_info_message(
                    f"Scheduler [ExecuteExpiredEmail] - Success - Executing expired email: {item.label}"
                )
                send_secure_email(item)
                send_owner_notice(item)
                item.executed_at = datetime.now(timezone.utc)
                item.is_enabled = False
                db.session.commit()
                log_info_message(
                    f"Scheduler [ExecuteExpiredEmail] - Success - Executed and disabled email: {item.label}"
                )
            except Exception as e:
                db.session.rollback()
                log_error_message(
                    f"ERROR - Scheduler [ExecuteExpiredEmail] - Failure - Error executing email '{item.label}': {e}\n{traceback.format_exc()}"
                )


# ---------------------------------------------------------------------
# create_daily_backup
# ---------------------------------------------------------------------
def create_daily_backup():
    """
    Create a new daily database backup and log the result.
    """
    try:
        path = create_backup()
        log_info_message(f"Scheduler [DailyBackup] - Success - Daily backup created: {path}")
    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [DailyBackup] - Failure - Failed to create daily backup: {e}\n{traceback.format_exc()}"
        )


# ---------------------------------------------------------------------
# execute_due_reminders
# ---------------------------------------------------------------------
def execute_due_reminders():
    now = datetime.now(timezone.utc)
    reminders = Reminder.query.filter_by(is_enabled=True).all()
    log_info_message(
        f"Scheduler [ExecuteDueReminders] - Success - Found {len(reminders)} enabled reminders to check"
    )

    for reminder in reminders:
        log_info_message(
            f"Scheduler [ExecuteDueReminders] - Success - Evaluating reminder: {reminder.label}"
        )

        if not reminder.is_enabled or not reminder.start_at:
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — not enabled or missing start_at"
            )
            continue

        if reminder.start_at.tzinfo is None:
            reminder.start_at = reminder.start_at.replace(tzinfo=timezone.utc)

        if reminder.start_at > now:
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — start_at in future: {reminder.start_at}"
            )
            continue

        if reminder.max_occurrences and reminder.occurrences_sent >= reminder.max_occurrences:
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — max occurrences reached ({reminder.occurrences_sent})"
            )
            reminder.is_enabled = False
            db.session.commit()
            continue

        if reminder.end_at and now >= reminder.end_at:
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — past end date {reminder.end_at}"
            )
            reminder.is_enabled = False
            db.session.commit()
            continue

        if reminder.recurrence_rule:
            rule = rrulestr(reminder.recurrence_rule, dtstart=reminder.start_at)
            next_occurrence = rule.after(reminder.last_sent_at or reminder.start_at, inc=True)

            if not next_occurrence or next_occurrence > now:
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — next occurrence is {next_occurrence}"
                )
                continue
        else:
            if reminder.last_sent_at:
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — already sent one-time reminder"
                )
                continue

        try:
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Success - Sending reminder: {reminder.label}"
            )

            if reminder.apprise_destinations:
                execute_apprise(reminder)
            else:
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — No Apprise destinations"
                )

            if reminder.webhooks:
                execute_webhooks(reminder)
            else:
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — No Webhooks"
                )

            if reminder.smtp_configs:
                send_reminder_email(reminder)
            else:
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - Skipping {reminder.label} — No SMTP config"
                )

            reminder.last_sent_at = now
            reminder.occurrences_sent += 1

            if not reminder.recurrence_rule:
                reminder.is_enabled = False
                log_info_message(
                    f"Scheduler [ExecuteDueReminders] - One-time reminder disabled: {reminder.label}"
                )

            db.session.commit()
            log_info_message(
                f"Scheduler [ExecuteDueReminders] - Success - Reminder sent: {reminder.label}"
            )

        except Exception as e:
            db.session.rollback()
            log_error_message(
                f"ERROR - Scheduler [ExecuteDueReminders] - Failure - Error sending reminder '{reminder.label}': {e}\n{traceback.format_exc()}"
            )
