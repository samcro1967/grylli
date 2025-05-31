# ---------------------------------------------------------------------
# i18n.py
# app/init/i18n.py
# Babel Configuration (i18n) for Flask application factory.
# ---------------------------------------------------------------------

import os


def setup_i18n(app):
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(app.root_path, "translations")
    app.config["BABEL_DEFAULT_DOMAIN"] = "messages"
