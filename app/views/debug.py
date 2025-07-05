"""
# ---------------------------------------------------------------------
# debug.py
# app/views/debug.py
# Blueprint for debugging front end
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_info_message

bp = Blueprint("debug", __name__)


@bp.route("layout", strict_slashes=False)
@login_required
def layout_debug():
    log_info_message(f"User '{current_user.username}' accessed the layout debug tool.")
    return render_template("debug/layout_debug.html", current_user=current_user)
