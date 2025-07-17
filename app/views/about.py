"""
# ---------------------------------------------------------------------
# about.py
# app/views/about.py
# Blueprint for rendering the About page in Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

# ---------------------------------------------------------------------
# Blueprint Configuration
# ---------------------------------------------------------------------

bp = Blueprint("about", __name__)


# ---------------------------------------------------------------------
# Route: /about
# ---------------------------------------------------------------------
@bp.route("about", methods=["GET"], strict_slashes=False)
@login_required
def show_about():
    """
    Renders the About page with HTMX-aware full and partial support.
    """
    log_info_message(f"Access - {current_user.username} - About")

    template = "about_partial.html" if request.headers.get("HX-Request") else "about_full.html"
    return render_template(template)
