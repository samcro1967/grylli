"""
# ---------------------------------------------------------------------
# system_settings.py
# app/views/system_settings.py
# View for displaying global/system config values (read-only for now).
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import login_required

import app.config as project_config
from app.views.auth import admin_required

bp = Blueprint("system_settings", __name__)


@bp.route("/")
@login_required
@admin_required
def view_app_config():
    # Show only ALL_CAPS settings from your config.py
    my_keys = [k for k in dir(project_config) if k.isupper() and not k.startswith("_")]
    config_items = {k: getattr(project_config, k) for k in my_keys}
    return render_template("admin/system_settings.html", config=config_items)
