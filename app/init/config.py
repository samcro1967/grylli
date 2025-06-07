"""
# ---------------------------------------------------------------------
# config.py
# app/init/config.py
# App Config & ENV Overrides for Flask application factory.
# ---------------------------------------------------------------------
"""

import os

from app.utils.logging import log_debug_message


def configure_app(app, config_override=None):
    """
    Configure the Flask app with environment or override settings.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # App Config & ENV Overrides
    # -------------------------------------------
    if config_override:
        app.config.update(config_override)
        log_debug_message("[config] Using config override dictionary")
    else:
        config_path = os.path.join(app.root_path, "config.py")
        app.config.from_pyfile(config_path)
        log_debug_message(f"[config] Loaded config from file: {config_path}")

    app.config["SECRET_KEY"] = os.environ.get("FLASK_APP_KEY") or app.config.get("SECRET_KEY")
    log_debug_message("[config] SECRET_KEY loaded (value hidden for security)")
