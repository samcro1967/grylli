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
from app.config import LOG_FILE_PATH, UI_LOG_LINE_LIMIT
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required

bp = Blueprint("reports", __name__)

LOG_PATH = LOG_FILE_PATH

# Route to display the full report (tabs)
@bp.route("/", strict_slashes=False)
@admin_required
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
@admin_required
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
@admin_required
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


@bp.route("/logs/", strict_slashes=False)
@login_required
@admin_required
def report_logs_full():
    """
    Displays the Application Logs tab under Admin Reports.
    """
    log_info_message(f"Access - {current_user.username} - Logs")

    level_filter = request.args.get("level", "").strip().upper()
    text_filter = request.args.get("text", "").strip().lower()
    after_filter = request.args.get("after", "").strip()
    sort_key = request.args.get("sort", "").strip()

    after_dt = None
    if after_filter:
        try:
            after_dt = datetime.fromisoformat(after_filter)
        except ValueError:
            pass

    log_entries = []
    log_path = LOG_FILE_PATH

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for raw_line in reversed(f.readlines()):
                line = raw_line.strip()

                if not line[:4].isdigit() or " - " not in line or line.count(" - ") < 2:
                    continue

                parts = line.split(" - ", 2)
                if len(parts) < 3:
                    continue

                timestamp, level, message = parts
                if level_filter and level.upper() != level_filter:
                    continue
                if text_filter and text_filter not in message.lower():
                    continue
                if after_dt:
                    try:
                        log_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S,%f")
                        if log_time < after_dt:
                            continue
                    except Exception:
                        continue

                log_entries.append((timestamp, level, message))
                if len(log_entries) >= UI_LOG_LINE_LIMIT * 2:
                    break

        reverse = False
        if sort_key.startswith("-"):
            reverse = True
            sort_key = sort_key[1:]

        if sort_key == "timestamp":
            log_entries.sort(key=lambda e: e[0], reverse=reverse)
        elif sort_key == "level":
            log_entries.sort(key=lambda e: e[1], reverse=reverse)

        log_entries = [f"{ts} - {lvl} - {msg}" for ts, lvl, msg in log_entries[:UI_LOG_LINE_LIMIT]]

    except FileNotFoundError:
        log_entries = ["⚠️ Log file not found."]
    except Exception as e:
        log_entries = [f"⚠️ Error reading log file: {e}"]

    if request.headers.get("HX-Request"):
        return render_template(
            "admin/reports/report_logs_partial.html",
            logs=log_entries,
            UI_LOG_LINE_LIMIT=UI_LOG_LINE_LIMIT
        )
    else:
        return render_template(
            "admin/reports/reports_full.html",
            active_tab="logs"
        )
