"""
# ---------------------------------------------------------------------
# help.py
# app/views/help.py
# Central Help page for Grylli
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("help", __name__)


# ---------------------------------------------------------------------
# Route: /help
# ---------------------------------------------------------------------
@bp.route("help", methods=["GET"], strict_slashes=False)
@login_required
def show_help():
    """
    Renders the Help page, supporting HTMX-aware partial rendering.

    Returns:
        str: Rendered HTML for the Help page.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Help")

        template = "help_partial.html" if request.headers.get("HX-Request") else "help_full.html"
        return render_template(template)
    except Exception as e:
        log_exception_with_traceback("Help page failed to load", e)
        flash(_("An error occurred while loading the help page."), "danger")
        return redirect(url_for("home.index"))
