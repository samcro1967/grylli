"""
# ---------------------------------------------------------------------
# dashboard.py
# app/utils/dashboard.py
# Dashboard utilities
# ---------------------------------------------------------------------
"""

from app.models import Message, EmailMessage
from datetime import datetime, timezone, timedelta

def is_checkin_due(last_checkin, interval_minutes, grace_minutes):
    """
    True if check-in is within grace window (past due but not executed).
    """
    if not last_checkin or not interval_minutes or not grace_minutes:
        return False

    now = datetime.now(timezone.utc)
    due_at = last_checkin.replace(tzinfo=timezone.utc) + timedelta(minutes=interval_minutes)
    grace_until = due_at + timedelta(minutes=grace_minutes)

    return due_at <= now < grace_until

def get_due_checkin_count(user_id):
    """
    Returns the number of enabled messages/emails that are currently due for check-in.
    """
    messages = Message.query.filter_by(user_id=user_id, is_enabled=True).all()
    emails = EmailMessage.query.filter_by(user_id=user_id, is_enabled=True).all()

    count = 0
    for m in messages:
        if is_checkin_due(m.last_checkin, m.checkin_interval_minutes, m.grace_period_minutes):
            count += 1
    for e in emails:
        if is_checkin_due(e.last_checkin, e.checkin_interval_minutes, e.grace_period_minutes):
            count += 1
    return count
