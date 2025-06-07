"""
# ---------------------------------------------------------------------
# scheduler.py
# app/services/scheduler/scheduler.py
# Core scheduling logic to check for reminders and execute actions
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
from datetime import datetime, timedelta

from dateutil.rrule import rrulestr

from app.extensions import db
from app.models import EmailMessage, Message, Reminder, User, UserMailSettings
from app.services.scheduler.apprise_utils import execute_apprise
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

    1. Iterates all enabled messages and secure emails to check if a reminder needs to be sent.
    2. Iterates all enabled messages and secure emails to check if they have expired.
    """
    find_messages_needing_checkin_reminder()
    find_expired_items()


# ---------------------------------------------------------------------
# find_messages_needing_checkin_reminder
# ---------------------------------------------------------------------
def find_messages_needing_checkin_reminder():
    """
    Check all enabled messages and secure emails to determine if a check-in reminder should be sent.

    - If the check-in interval has elapsed since last check-in and no reminder was sent, send reminder.
    - Updates reminder_sent_at to prevent duplicate reminders.
    """
    now = datetime.utcnow()
    messages = Message.query.filter_by(is_enabled=True).all()
    emails = EmailMessage.query.filter_by(is_enabled=True).all()

    for item in messages + emails:
        if item.checkin_interval_minutes is None or item.last_checkin is None:
            continue

        delta = timedelta(minutes=item.checkin_interval_minutes)
        if now - item.last_checkin >= delta:
            # ✅ Only send reminder if it hasn't already been sent
            if item.reminder_sent_at is None:

                user = User.query.get(item.user_id)
                if user:
                    # Set reminder_sent_at BEFORE sending email to prevent duplicates
                    item.reminder_sent_at = now
                    db.session.commit()

                    send_checkin_email(user, item)
                else:
                    log_error_message(f"❌ Cannot send reminder — user {item.user_id} not found")


# ---------------------------------------------------------------------
# find_expired_items
# ---------------------------------------------------------------------
def find_expired_items():
    """
    Check all enabled messages and secure emails for expiration.

    - If reminder_sent_at is set and grace period has elapsed, execute and disable the item.
    - Handles both regular messages and EmailMessage.
    """
    now = datetime.utcnow()
    messages = Message.query.filter_by(is_enabled=True).all()
    emails = EmailMessage.query.filter_by(is_enabled=True).all()

    # --- Expired Messages ---
    for item in messages:
        if item.executed_at is not None:
            log_info_message(f"⏭️ Skipping {item.label} — already executed")
            continue
        if item.grace_period_minutes is None:
            log_info_message(f"⏭️ Skipping {item.label} — no grace period")
            continue
        if item.last_checkin is None:
            log_info_message(f"⏭️ Skipping {item.label} — no last check-in")
            continue
        if item.reminder_sent_at is None:
            log_info_message(f"⏭️ Skipping {item.label} — no reminder sent yet")
            continue
        if now - item.reminder_sent_at < timedelta(minutes=item.grace_period_minutes):
            log_info_message(f"⏭️ Skipping {item.label} — grace period not yet elapsed")
            continue

        grace = timedelta(minutes=item.checkin_interval_minutes + item.grace_period_minutes)
        if now - item.last_checkin >= grace:
            try:
                log_info_message(f"💀 Executing expired message: {item.label}")
                execute_apprise(item)
                execute_webhooks(item)
                send_owner_notice(item)
                item.executed_at = datetime.utcnow()
                item.is_enabled = False
                db.session.commit()
                log_info_message(f"✅ Executed and disabled message: {item.label}")
            except Exception as e:
                db.session.rollback()
                log_error_message(f"❌ Error executing message '{item.label}': {str(e)}")

    # --- Expired Secure Emails ---
    for item in emails:
        if item.executed_at is not None:
            log_info_message(f"⏭️ Skipping {item.label} — already executed")
            continue
        if item.grace_period_minutes is None:
            log_info_message(f"⏭️ Skipping {item.label} — no grace period")
            continue
        if item.last_checkin is None:
            log_info_message(f"⏭️ Skipping {item.label} — no last check-in")
            continue
        if item.reminder_sent_at is None:
            log_info_message(f"⏭️ Skipping {item.label} — no reminder sent yet")
            continue
        if now - item.reminder_sent_at < timedelta(minutes=item.grace_period_minutes):
            log_info_message(f"⏭️ Skipping {item.label} — grace period not yet elapsed")
            continue

        grace = timedelta(minutes=item.checkin_interval_minutes + item.grace_period_minutes)
        if now - item.last_checkin >= grace:
            try:
                log_info_message(f"📤 Executing expired email: {item.label}")
                send_secure_email(item)
                send_owner_notice(item)
                item.executed_at = datetime.utcnow()
                item.is_enabled = False
                db.session.commit()
                log_info_message(f"✅ Executed and disabled email: {item.label}")
            except Exception as e:
                db.session.rollback()
                log_error_message(f"❌ Error executing email '{item.label}': {str(e)}")


# ---------------------------------------------------------------------
# Backup Task: Create DB backup daily
# ---------------------------------------------------------------------
from app.services.scheduler.backup_utils import create_backup


def create_daily_backup():
    """
    Create a new daily database backup and log the result.

    Logging:
        - log_info_message if backup succeeds.
        - log_error_message if backup fails.
    """
    try:
        path = create_backup()
        log_info_message(f"🗂️ Daily backup created: {path}")
    except Exception as e:
        log_error_message(f"❌ Failed to create daily backup: {e}")


# ---------------------------------------------------------------------
# Reminder Task
# ---------------------------------------------------------------------
def execute_due_reminders():
    """
    Execute enabled reminders that are due, based on one-time start time.

    For now:
    - Fires if start_at <= now
    - Skips if already sent
    - Disables after sending if no recurrence
    """
    now = datetime.utcnow()
    reminders = Reminder.query.filter_by(is_enabled=True).all()
    log_info_message(f"📋 Found {len(reminders)} enabled reminders to check")

    for reminder in reminders:
        log_info_message(f"🔎 Evaluating reminder: {reminder.label}")

        if not reminder.is_enabled:
            log_info_message(f"⏭️ Skipping {reminder.label} — is_enabled is False")
            continue  # Redundant safeguard

        if not reminder.start_at:
            log_info_message(f"⏭️ Skipping {reminder.label} — no start_at set")
            continue

        if reminder.start_at > now:
            log_info_message(
                f"⏭️ Skipping {reminder.label} — start_at is in the future: {reminder.start_at}"
            )
            continue

        # ---- MAX OCCURRENCES CHECK ----
        if reminder.max_occurrences and reminder.occurrences_sent >= reminder.max_occurrences:
            log_info_message(
                f"⏭️ Skipping {reminder.label} — reached max occurrences ({reminder.occurrences_sent} / {reminder.max_occurrences})"
            )
            reminder.is_enabled = False  # Optionally auto-disable
            db.session.commit()
            continue

        # ---- END DATE CHECK ----
        if reminder.end_at and now >= reminder.end_at:
            log_info_message(f"⏭️ Skipping {reminder.label} — past end date ({reminder.end_at})")
            reminder.is_enabled = False  # Optionally auto-disable
            db.session.commit()
            continue

        if reminder.recurrence_rule:
            rule = rrulestr(reminder.recurrence_rule, dtstart=reminder.start_at)
            next_occurrence = rule.after(reminder.last_sent_at or reminder.start_at, inc=True)

            if not next_occurrence or next_occurrence > now:
                log_info_message(
                    f"⏭️ Skipping {reminder.label} — next occurrence is {next_occurrence}"
                )
                continue
        else:
            # one-time reminder
            if reminder.last_sent_at:
                log_info_message(f"⏭️ Skipping {reminder.label} — already sent and no recurrence")
                continue

        try:
            log_info_message(f"📆 Sending reminder: {reminder.label}")

            # --- Send to explicitly assigned destinations only ---
            if reminder.apprise_destinations:
                execute_apprise(reminder)
            else:
                log_info_message(f"📭 No Apprise destinations assigned for {reminder.label}")

            if reminder.webhooks:
                execute_webhooks(reminder)
            else:
                log_info_message(f"📭 No Webhook destinations assigned for {reminder.label}")

            if reminder.smtp_configs:
                send_reminder_email(reminder)
            else:
                log_info_message(
                    f"📭 No SMTP config assigned for reminder '{reminder.label}' — skipping email"
                )

            # --- Update reminder state ---
            reminder.last_sent_at = now
            reminder.occurrences_sent += 1

            if not reminder.recurrence_rule:
                reminder.is_enabled = False
                log_info_message(
                    f"🔕 Reminder '{reminder.label}' is one-time — disabling after send."
                )

            log_info_message(
                f"📝 Committing reminder: {reminder.label}, is_enabled={reminder.is_enabled}"
            )
            db.session.commit()
            log_info_message(f"✅ Reminder sent: {reminder.label}")

        except Exception as e:
            db.session.rollback()
            log_error_message(f"❌ Error sending reminder '{reminder.label}': {str(e)}")
