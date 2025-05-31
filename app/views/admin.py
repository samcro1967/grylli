"""
# ---------------------------------------------------------------------
# admin.py
# app/views/admin.py
# Admin landing page view and blueprint for Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import login_required

from app.views.auth import admin_required

bp = Blueprint("admin", __name__)


@bp.route("/admin/")
@login_required
@admin_required
def admin_landing():
    return render_template("admin/index.html")
