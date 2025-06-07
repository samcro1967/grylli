"""
# ---------------------------------------------------------------------
# index.py
# app/views/index.py
# Blueprint for application landing page (index view).
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

bp = Blueprint("index", __name__)


@bp.route("/")
@login_required
def index():
    """
    Render the landing page for the application.

    This is the first page seen by an authenticated user when they visit
    the root URL of the application.

    :returns: rendered HTML template
    """
    log_info_message(f"User '{current_user.username}' accessed the index page.")
    return render_template("index.html")
