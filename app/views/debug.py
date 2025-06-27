"""
# ---------------------------------------------------------------------
# debug.py
# app/views/debug.py
# Blueprint for debugging front end
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

bp = Blueprint("debug", __name__)


@bp.route("/layout")
@login_required
def layout_debug():
    return render_template("debug/layout_debug.html", current_user=current_user)
