"""
# ---------------------------------------------------------------------
# index.py
# app/views/index.py
# Blueprint for application landing page (index view).
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("home", __name__)


@bp.route("/")
@login_required
def index():
    """
    Render the landing page for the application.

    This is the first page seen by an authenticated user when they visit
    the root URL of the application.

    :returns: rendered HTML template
    """
    try:
        log_info_message(f"User '{current_user.username}' accessed the index page.")
        return render_template("index.html")
    except Exception as e:
        log_exception_with_traceback("Index page failed to load", e)
        flash(_("An error occurred while loading the index page."), "danger")
        return redirect(url_for("auth.login"))
