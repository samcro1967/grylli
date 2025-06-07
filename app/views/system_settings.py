"""
# ---------------------------------------------------------------------
# system_settings.py
# app/views/system_settings.py
# View for displaying global/system config values (read-only for now).
# ---------------------------------------------------------------------
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

import app.config as project_config
from app.utils.logging import log_info_message
from app.views.auth import admin_required

bp = Blueprint("system_settings", __name__)


# ---------------------------------------------------------------------
# View:  System Settings
# ---------------------------------------------------------------------
@bp.route("/")
@login_required
@admin_required
def view_app_config():
    """
    Renders the system settings template for the admin to view global config values.

    The template currently shows only ALL_CAPS settings from your config.py.

    :return: The rendered template.
    """
    log_info_message(f"Admin '{current_user.username}' accessed system settings.")

    # Show only ALL_CAPS settings from your config.py
    my_keys = [k for k in dir(project_config) if k.isupper() and not k.startswith("_")]
    config_items = {k: getattr(project_config, k) for k in my_keys}
    return render_template("admin/system_settings.html", config=config_items)
