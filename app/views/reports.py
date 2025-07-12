# ---------------------------------------------------------------------
# reports.py
# app/views/reports.py
# Admin reports view (tabbed layout for user account and scheduler info)
# ---------------------------------------------------------------------

import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("reports", __name__)


# Route to display the full report (tabs)
@bp.route("/", strict_slashes=False)
@login_required
def reports_full():
    try:
        log_info_message(f"Access - {current_user.username} - User Reports")
        active_tab = request.args.get("tab", "accounts")

        if request.headers.get("HX-Request"):
            return render_template("admin/reports/reports_tabs.html", active_tab=active_tab)

        return render_template("admin/reports/reports_full.html", active_tab=active_tab)
    except Exception as e:
        log_exception_with_traceback("Failed to load user reports page", e)
        return "", 204


# Route to display accounts report (using partial)
@bp.route("/accounts/", strict_slashes=False)
@login_required
def report_accounts_full():
    try:
        # Load all users and eager-load their relationships
        users = (
            User.query.options(
                db.joinedload(User.messages),
                db.joinedload(User.email_messages),
                db.joinedload(User.reminders),
            )
            .order_by(User.username)
            .all()
        )

        enriched_users = []
        for user in users:
            enriched_users.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_enabled": user.is_enabled,
                    "created_at": user.created_at,
                    "mfa_enabled": user.mfa_enabled,
                    "locked_until": user.locked_until,
                    "notification_count": len(user.messages),
                    "email_count": len(user.email_messages),
                    "reminder_count": len(user.reminders),
                }
            )

        if request.headers.get("HX-Request"):
            return render_template("admin/reports/report_accounts_partial.html", users=enriched_users)

        # ⬅️ Return full layout on direct link
        return render_template("admin/reports/reports_full.html", active_tab="accounts")

    except Exception as e:
        log_exception_with_traceback("Failed to load report_accounts_full", e)
        return "", 204

# Route to display scheduler report (using partial)
@bp.route("/scheduler/", strict_slashes=False)
@login_required
def report_scheduler_full():
    try:
        log_info_message(f"Access - {current_user.username} - Scheduler Activity Report")

        logs = get_scheduler_logs()
        max_entries = current_app.config["SCHEDULER_LOG_DISPLAY_LIMIT"]

        # If HTMX request, return just the tab content
        if request.headers.get("HX-Request"):
            return render_template("admin/reports/report_scheduler_partial.html",
                                   logs=logs,
                                   max_entries=max_entries)

        # Otherwise return the full page with correct tab active
        return render_template("admin/reports/reports_full.html", active_tab="scheduler")

    except Exception as e:
        log_exception_with_traceback("Failed to load scheduler report tab", e)
        return "", 204

def get_scheduler_logs():
    """
    Extracts scheduler activity lines from the grylli log file.
    Format:
    TIMESTAMP - LEVEL - Scheduler [Job] - Status - Detail
    """
    import os

    log_path = os.path.join(os.getcwd(), "data", "grylli.log")
    logs = []
    max_entries = current_app.config.get("SCHEDULER_LOG_DISPLAY_LIMIT", 350)

    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as file:
                for line in file:
                    if "Scheduler [" in line and " - " in line:
                        parts = line.strip().split(" - ", 4)
                        if len(parts) != 5:
                            continue  # Skip malformed lines

                        logs.append({
                            "timestamp": parts[0].strip(),
                            "level": parts[1].strip(),
                            "job_name": parts[2].strip(),
                            "status": parts[3].strip(),
                            "detail": parts[4].strip(),
                        })

        # Sort by timestamp descending and cap
        return list(reversed(logs))[:max_entries]

    except Exception as e:
        from app.utils.logging import log_exception_with_traceback
        log_exception_with_traceback("Error reading scheduler logs", e)
        return []
