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
from app.views.auth import admin_required

bp = Blueprint("debug", __name__)


@bp.route("layout", strict_slashes=False)
@admin_required
@login_required
def layout_debug():
    log_info_message(f"Access - {current_user.username} - Layout Debug Tool")
    return render_template("debug/layout_debug.html", current_user=current_user)
