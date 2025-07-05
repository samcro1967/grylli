# ---------------------------------------------------------------------
# system_settings.py
# app/views/system_settings.py
# View for displaying global/system config values (read-only for now).
# ---------------------------------------------------------------------

from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

import app.config as project_config
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required

bp = Blueprint("system_settings", __name__)


# ---------------------------------------------------------------------
# View:  System Settings
# ---------------------------------------------------------------------
from pathlib import Path

# ...


@bp.route("overview/", strict_slashes=False)
@login_required
@admin_required
def view_app_config():
    """
    Renders the system settings template for the admin to view global config values.
    Returns a partial if requested via HTMX.
    """
    try:
        log_info_message(f"Admin '{current_user.username}' accessed system settings.")

        my_keys = [k for k in dir(project_config) if k.isupper() and not k.startswith("_")]
        config_items = {}
        for key in my_keys:
            value = getattr(project_config, key)
            if isinstance(value, str) and "/grylli" in value:
                # Strip everything before the /grylli part
                value = str(Path(value).as_posix())
                value = value[value.find("/grylli") :]
            config_items[key] = value

        if request.headers.get("HX-Request"):
            return render_template("admin/system_settings_partial.html", config=config_items)
        return render_template("admin/system_settings_full.html", config=config_items)

    except Exception as e:
        log_exception_with_traceback("Failed to render system settings", e)
        flash(_("Failed to load system settings."), "danger")
        return redirect(url_for("home.index"))
