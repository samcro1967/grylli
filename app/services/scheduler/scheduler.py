"""
# ---------------------------------------------------------------------
# scheduler.py
# app/services/scheduler/scheduler.py
# Core scheduling logic to check for reminders and execute actions
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
from datetime import datetime, timedelta

from app.extensions import db
from app.models import Message, EmailMessage, User, UserMailSettings
from app.services.scheduler.apprise_utils import execute_apprise
from app.services.scheduler.email_utils import (
    send_checkin_email,
    send_owner_notice,
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
# End of file: app/services/scheduler/scheduler.py
# ---------------------------------------------------------------------
