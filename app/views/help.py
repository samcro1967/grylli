"""
# ---------------------------------------------------------------------
# help.py
# app/views/help.py
# Central Help page for Grylli
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

bp = Blueprint("help", __name__)


# ---------------------------------------------------------------------
# Route: /help
# ---------------------------------------------------------------------
@bp.route("/help", methods=["GET"])
@login_required
def show_help():
    """
    Renders the Help page, which provides an overview of key Grylli features
    and links to configuration areas for notifications, emails, SMTP setup,
    Apprise integration, and system security practices.

    Returns:
        str: Rendered HTML for the Help page.
    """
    log_info_message(f"User '{current_user.username}' accessed the Help page.")
    return render_template("help.html")
