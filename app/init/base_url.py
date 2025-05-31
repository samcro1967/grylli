"""
# ---------------------------------------------------------------------
# base_url.py
# app/init/base_url.py
# Get base_url if set by user
# ---------------------------------------------------------------------
"""

import os

from app.utils.logging import log_info_message


def setup_base_url(app):
    """
    Set up BASE_URL and DEFAULT_LANGUAGE in app.config, matching original order.
    """
    base_url = os.environ.get("BASE_URL", "/").rstrip("/")
    app.config["BASE_URL"] = base_url
    log_info_message(("Using base URL prefix: ") + base_url)

    app.config["DEFAULT_LANGUAGE"] = os.environ.get("DEFAULT_LANGUAGE", "en")
    log_info_message(("Default language set to: ") + app.config["DEFAULT_LANGUAGE"])

    # Process the prefix for later use
    if base_url == "/":
        url_prefix = ""
    elif base_url and not base_url.startswith("/"):
        url_prefix = "/" + base_url
    else:
        url_prefix = base_url
    app.config["URL_PREFIX"] = url_prefix
