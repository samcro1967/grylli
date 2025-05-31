"""
# ---------------------------------------------------------------------
# config.py
# app/init/config.py
# App Config & ENV Overrides for Flask application factory.
# ---------------------------------------------------------------------
"""

import os


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
    else:
        app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    app.config["SECRET_KEY"] = os.environ.get("FLASK_APP_KEY") or app.config.get("SECRET_KEY")
