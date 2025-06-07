# ---------------------------------------------------------------------
# privacy.py
# app/views/privacy.py
# Route to display the Privacy Notice page.
# ---------------------------------------------------------------------

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

bp = Blueprint("privacy", __name__)


# ---------------------------------------------------------------------
# View: Show privacy
# ---------------------------------------------------------------------
@bp.route("/")
@login_required
def show_privacy():
    """
    Renders the Privacy Notice page.

    Returns:
        str: Rendered HTML for the Privacy Notice page.
    """
    log_info_message(f"User '{current_user.username}' viewed the Privacy Notice page.")
    return render_template("privacy.html")
