"""
# ---------------------------------------------------------------------
# about.py
# app/views/about.py
# Blueprint for rendering the About page in Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

# ---------------------------------------------------------------------
# Blueprint Configuration
# ---------------------------------------------------------------------

bp = Blueprint("about", __name__)


# ---------------------------------------------------------------------
# Route: /about
# ---------------------------------------------------------------------
@bp.route("/about", methods=["GET"])
@login_required
def show_about():
    """
    Renders the About page, including version and GitHub info.

    Returns:
        str: Rendered HTML for the About page.
    """
    log_info_message(f"User '{current_user.username}' viewed the About page.")
    return render_template("about.html")
