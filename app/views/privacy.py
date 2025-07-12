# ---------------------------------------------------------------------
# privacy.py
# app/views/privacy.py
# Route to display the Privacy Notice page.
# ---------------------------------------------------------------------

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("privacy", __name__)


# ---------------------------------------------------------------------
# View: Show privacy
# ---------------------------------------------------------------------
@bp.route("", strict_slashes=False)
@login_required
def show_privacy():
    """
    Renders the Privacy Notice page, supporting full or partial HTMX response.

    Returns:
        str: Rendered HTML for the Privacy Notice page.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Privacy Notice")
        template = (
            "privacy_partial.html" if request.headers.get("HX-Request") else "privacy_full.html"
        )
        return render_template(template)
    except Exception as e:
        log_exception_with_traceback("Error rendering the Privacy Notice page", e)
        flash(_("An error occurred while loading the Privacy Notice."), "danger")
        return redirect(url_for("home.index"))
