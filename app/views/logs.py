# ---------------------------------------------------------------------
# logs.py — app/views/logs.py
# View for the system admin log viewer with HTMX filtering and sorting
# ---------------------------------------------------------------------

import os
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_babel import _
from flask_login import current_user, login_required

from app.config import LOG_FILE_PATH, UI_LOG_LINE_LIMIT
from app.utils.logging import log_info_message
from app.views.auth import admin_required

bp = Blueprint("logs", __name__, url_prefix="/grylli/admin/logs")

LOG_PATH = LOG_FILE_PATH


@bp.route("/", methods=["GET"])
@login_required
@admin_required
def view_logs():
    """
    Displays application logs with optional HTMX filtering and sorting.
    """
    log_info_message(f"Admin '{current_user.username}' accessed recent log viewer")

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

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for raw_line in reversed(f.readlines()):
                line = raw_line.strip()

                if not line[:4].isdigit() or " - " not in line or line.count(" - ") < 2:
                    continue  # skip invalid or non-app lines

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

        # Sort results
        reverse = False
        if sort_key.startswith("-"):
            reverse = True
            sort_key = sort_key[1:]

        if sort_key == "timestamp":
            log_entries.sort(key=lambda e: e[0], reverse=reverse)
        elif sort_key == "level":
            log_entries.sort(key=lambda e: e[1], reverse=reverse)

        # Recombine for output
        log_entries = [f"{ts} - {lvl} - {msg}" for ts, lvl, msg in log_entries[:UI_LOG_LINE_LIMIT]]

    except FileNotFoundError:
        log_entries = ["⚠️ Log file not found."]
    except Exception as e:
        log_entries = [f"⚠️ Error reading log file: {e}"]

    template = (
        "admin/logs.html"
        if not request.headers.get("HX-Request")
        else "admin/partials/logs_table.html"
    )
    return render_template(template, logs=log_entries, UI_LOG_LINE_LIMIT=UI_LOG_LINE_LIMIT)
