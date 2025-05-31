"""
# ---------------------------------------------------------------------
# index.py
# app/views/index.py
# Blueprint for application landing page (index view).
# ---------------------------------------------------------------------
"""

from flask import Blueprint, abort, current_app, jsonify, render_template
from flask_babel import gettext
from flask_login import login_required

from app.utils.locale import get_locale
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
    return render_template("index.html")
