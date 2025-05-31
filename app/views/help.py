"""
# ---------------------------------------------------------------------
# help.py
# app/views/help.py
# Central Help page for Grylli
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import login_required

# ---------------------------------------------------------------------
# Blueprint Configuration
# ---------------------------------------------------------------------

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
    return render_template("help.html")
