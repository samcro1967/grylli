"""
# ---------------------------------------------------------------------
# index.py
# app/views/index.py
# Blueprint for application landing page (index view).
# ---------------------------------------------------------------------
"""

import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
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
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("home", __name__)


@bp.route("overview/", strict_slashes=False)
@login_required
def index():
    try:
        log_info_message(f"User '{current_user.username}' accessed dashboard")
        tab = request.args.get("tab", "config")  # ✅ Define it here
        stats = get_dashboard_stats()

        if request.headers.get("HX-Request"):
            # Return full tab layout for HTMX (not just partial)
            return render_template("dashboard/dashboard_tabs.html", stats=stats, active_tab=tab)

        # Full layout for standard loads
        return render_template("dashboard/dashboard_full.html", stats=stats, active_tab=tab)

    except Exception as e:
        log_exception_with_traceback("Failed to load dashboard", e)
        flash(_("Error loading dashboard"), "danger")
        return redirect(url_for("auth.login"))


def get_dashboard_stats():
    return {
        "reminders": Reminder.query.filter_by(user_id=current_user.id).all(),
        "emails": EmailMessage.query.filter_by(user_id=current_user.id).all(),
        "messages": Message.query.filter_by(user_id=current_user.id).all(),
        "apprise": AppriseURL.query.filter_by(user_id=current_user.id).all(),
        "webhooks": Webhook.query.filter_by(user_id=current_user.id).all(),
        "smtp": UserMailSettings.query.filter_by(user_id=current_user.id).all(),
    }


@bp.route("overview/config/", strict_slashes=False)
@login_required
def config_tab():
    """
    Renders the full dashboard view with the Config tab active,
    or just the Config partial if requested via HTMX.
    """
    try:
        log_info_message(f"User '{current_user.username}' accessed dashboard Config tab.")
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
    """
    Renders the full dashboard view with the Schedule tab active,
    or just the Schedule partial if requested via HTMX.
    """
    try:
        stats = get_dashboard_stats()
        log_info_message(f"User '{current_user.username}' accessed dashboard Schedule tab.")

        if request.headers.get("HX-Request"):
            return render_template("dashboard/partials/_schedule_partial.html", stats=stats)

        return render_template("dashboard/dashboard_full.html", stats=stats, active_tab="schedule")
    except Exception as e:
        log_exception_with_traceback("Failed to render schedule tab", e)
        return "", 204


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
        log_info_message(f"User '{current_user.username}' accessed dashboard Activity tab.")

        if request.headers.get("HX-Request"):
            return render_template("dashboard/partials/_activity_partial.html", entries=entries)

        return render_template("dashboard/dashboard_full.html", stats=stats, entries=entries, active_tab="activity")
    except Exception as e:
        log_exception_with_traceback("Failed to render activity tab", e)
        return "", 204


def get_user_activity_log(username, max_lines=200):
    log_path = current_app.config.get("LOG_FILE_PATH", "logs/grylli.log")

    if not os.path.exists(log_path):
        return []

    quoted = f"'{username}'"
    entries = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in reversed(f.readlines()):
            if quoted in line:
                parts = line.strip().split(" - ", 2)
                if len(parts) == 3:
                    timestamp, level, message = parts
                    entries.append(
                        {
                            "timestamp": timestamp,
                            "level": level,
                            "message": message,
                        }
                    )
            if len(entries) >= max_lines:
                break

    return list(reversed(entries))


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
