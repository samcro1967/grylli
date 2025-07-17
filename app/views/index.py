"""
# ---------------------------------------------------------------------
# index.py
# app/views/index.py
# Blueprint for application landing page (index view).
# ---------------------------------------------------------------------
"""

import os
from datetime import datetime, timezone, timedelta
import traceback

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for, send_from_directory

from flask_babel import _
from flask_login import current_user, login_required

from app.models import (
    AppriseURL,
    EmailMessage,
    Message,
    Reminder,
    UserMailSettings,
    Webhook,
)
from app.utils.logging import ALLOWED_USER_ACTIONS, log_exception_with_traceback, log_info_message
from app.utils.duration import format_minutes_as_duration_parts

bp = Blueprint("home", __name__)

@bp.route("/", strict_slashes=False)
def root_redirect():
    """
    Redirects /grylli/ to /grylli/overview/ to avoid 404 errors.
    """
    return redirect(url_for("home.index"))


@bp.route("overview/", strict_slashes=False)
@login_required
def index():
    try:
        log_info_message(f"Access - {current_user.username} - Dashboard")
        stats = get_dashboard_stats()

        if request.headers.get("HX-Request"):
            # Return full tab layout for HTMX (not just partial)
            return render_template("dashboard/dashboard_tabs.html", stats=stats, active_tab="config")

        # Full layout for standard loads
        return render_template("dashboard/dashboard_full.html", stats=stats, active_tab="config")

    except Exception as e:
        log_exception_with_traceback("Failed to load dashboard", e)
        flash(_("Error loading dashboard"), "danger")
        return redirect(url_for("auth.login"))


def get_dashboard_stats():
    """
    Collects statistics about the user's items (Reminders, Emails, Messages, Apprise URLs, Webhooks, SMTP).
    This is used to populate the dashboard with relevant user data, including linked items.
    """
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()
    messages = Message.query.filter_by(user_id=current_user.id).all()
    emails = EmailMessage.query.filter_by(user_id=current_user.id).all()
    apprise_urls = AppriseURL.query.filter_by(user_id=current_user.id).all()
    webhooks = Webhook.query.filter_by(user_id=current_user.id).all()
    smtp = UserMailSettings.query.filter_by(user_id=current_user.id).all()

    # Populate shortcut fields for reminders
    for reminder in reminders:
        reminder.apprise_links = reminder.apprise_destinations
        reminder.email_links = reminder.email_messages
        reminder.smtp_links = reminder.smtp_configs
        reminder.webhook_links = reminder.webhooks

    # Populate shortcut fields for messages
    for msg in messages:
        msg.apprise_links = msg.apprise_destinations
        msg.webhook_links = msg.webhooks

    # Populate shortcut fields for emails
    for email in emails:
        email.smtp_links = email.smtp_configs

    return {
        "reminders": reminders,
        "messages": messages,
        "emails": emails,
        "apprise": apprise_urls,
        "webhooks": webhooks,
        "smtp": smtp,
    }


@bp.route("overview/config/", strict_slashes=False)
@login_required
def config_tab():
    """
    Renders the full dashboard view with the Config tab active,
    or just the Config partial if requested via HTMX.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Dashboard Config")
        stats = get_dashboard_stats()

        if request.headers.get("HX-Request"):
            return render_template("dashboard/partials/_config_partial.html", stats=stats)

        return render_template("dashboard/dashboard_full.html", stats=stats, active_tab="config")
    except Exception as e:
        log_exception_with_traceback("Failed to render config tab", e)
        return "", 204


@bp.route("overview/schedule/", strict_slashes=False)
@login_required
def schedule_tab():
    try:
        stats = decorate_schedule_stats(get_dashboard_stats())
        log_info_message(f"Access - {current_user.username} - Dashboard Schedule")

        if request.headers.get("HX-Request"):
            return render_template("dashboard/partials/_schedule_partial.html", stats=stats)

        return render_template("dashboard/dashboard_full.html", stats=stats, active_tab="schedule")
    except Exception as e:
        log_exception_with_traceback("Failed to render schedule tab", e)
        return "", 204

def decorate_schedule_stats(stats):
    """
    Adds human-readable interval and grace period strings and check-in status to stats dict.
    """
    for item in stats.get("messages", []):
        item.interval_human = format_minutes_as_duration_parts(item.checkin_interval_minutes)
        item.grace_human = format_minutes_as_duration_parts(item.grace_period_minutes)
        item.is_checkin_due = is_checkin_due(item.last_checkin, item.checkin_interval_minutes, item.grace_period_minutes)

    for item in stats.get("emails", []):
        item.interval_human = format_minutes_as_duration_parts(item.checkin_interval_minutes)
        item.grace_human = format_minutes_as_duration_parts(item.grace_period_minutes)
        item.is_checkin_due = is_checkin_due(item.last_checkin, item.checkin_interval_minutes, item.grace_period_minutes)

    return stats

def is_checkin_due(last_checkin, interval_minutes, grace_minutes):
    """
    Returns True if check-in is due: past interval but still within grace.
    Handles both naive and aware datetimes by forcing everything to UTC aware.
    """
    if not last_checkin or not interval_minutes or not grace_minutes:
        return False

    # Ensure last_checkin is aware
    if last_checkin.tzinfo is None:
        last_checkin = last_checkin.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    due_at = last_checkin + timedelta(minutes=interval_minutes)
    grace_until = due_at + timedelta(minutes=grace_minutes)

    return due_at <= now < grace_until

@bp.route("overview/activity/", strict_slashes=False)
@login_required
def activity_tab():
    """
    Renders the full dashboard view with the Activity tab active,
    or just the Activity partial if requested via HTMX.
    """
    try:
        entries = get_user_activity_log(current_user.username)
        stats = get_dashboard_stats()
        log_info_message(f"Access - {current_user.username} - Dashboard Activity")

        if request.headers.get("HX-Request"):
            return render_template("dashboard/partials/_activity_partial.html", entries=entries)

        return render_template(
            "dashboard/dashboard_full.html", stats=stats, entries=entries, active_tab="activity"
        )
    except Exception as e:
        log_exception_with_traceback("Failed to render activity tab", e)
        return "", 204


MODULE_NAMES = {
    "Reminder",
    "Email",
    "Notification",
    "Apprise",
    "Webhook",
    "SMTP",
    "Account",
}


def get_user_activity_log(username, max_lines=500):
    log_path = current_app.config.get("LOG_FILE_PATH", "logs/grylli.log")
    if not os.path.exists(log_path):
        return []

    entries = []
    quoted = f"{username}"

    with open(log_path, "r", encoding="utf-8") as f:
        for line in reversed(f.readlines()):
            if f" - {quoted} - " not in line:
                continue

            # Try to split 6-part structured logs first
            parts = line.strip().split(" - ", 5)

            if len(parts) == 6:
                timestamp, level, category, action, user, message = parts
                if user != username:
                    continue
                if category in MODULE_NAMES and action in ALLOWED_USER_ACTIONS:
                    label = message.split(" | ", 1)[-1].strip()
                    entries.append(
                        {
                            "timestamp": timestamp.strip(),
                            "category": category.strip(),
                            "user": user.strip(),
                            "message": f"{action} - {label}",
                        }
                    )
            elif len(parts) == 5:
                timestamp, level, category, user, message = parts
                if user != username:
                    continue
                entries.append(
                    {
                        "timestamp": timestamp.strip(),
                        "category": category.strip(),
                        "user": user.strip(),
                        "message": message.strip(),
                    }
                )

            if len(entries) >= max_lines:
                break

    return entries


@bp.route("overview/linked_items/", strict_slashes=False)
@login_required
def linked_items_tab():
    """
    Renders the full dashboard view with the Linked Items tab active,
    or just the Linked Items partial if requested via HTMX.
    """
    try:
        # Fetch the dashboard stats (linked items and other stats)
        stats = get_dashboard_stats()
        log_info_message(f"Access - {current_user.username} - Dashboard Linked Items")

        if request.headers.get("HX-Request"):
            # Return only the linked items table partial if requested via HTMX
            return render_template("dashboard/partials/_linked_items_partial.html", stats=stats)

        # Render the full dashboard layout if it's a regular request
        return render_template(
            "dashboard/dashboard_full.html", stats=stats, active_tab="linked_items"
        )
    except Exception as e:
        log_exception_with_traceback("Failed to render linked items tab", e)
        return "", 204


@bp.route("/server-time")
@login_required
def server_time():
    """
    Returns the current server-local time and timezone, formatted for display.
    Used for header time display, refreshed via HTMX every 60s.
    """
    try:
        now = datetime.now().astimezone()
        return render_template("partials/server_time.html", now=now)
    except Exception as e:
        log_exception_with_traceback("Failed to render server time", e)
        return "", 204  # Fail silently for HTMX

# ---------------------------------------------------------------------
# Route: Service Worker (PWA)
# ---------------------------------------------------------------------
@bp.route("/service-worker.js")
def service_worker():
    """
    Serve the PWA service worker from the static directory.
    This avoids hardcoding the URL prefix like /grylli/static.
    """
    response = send_from_directory(
        current_app.static_folder,
        "service-worker.js",
        mimetype="application/javascript"
    )
    response.headers["Cache-Control"] = "no-cache"
    return response
