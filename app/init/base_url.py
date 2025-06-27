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
    raw_base_url = os.environ.get("BASE_URL", "/")
    log_info_message(f"📦 Raw BASE_URL from environment: {raw_base_url}")

    base_url = raw_base_url.rstrip("/")
    app.config["BASE_URL"] = base_url
    log_info_message(f"🌐 Normalized base URL: {base_url}")

    default_lang = os.environ.get("DEFAULT_LANGUAGE", "en")
    app.config["DEFAULT_LANGUAGE"] = default_lang
    log_info_message(f"🈯 Default language set to: {default_lang}")

    # Process the prefix for later use
    if base_url == "/":
        url_prefix = ""
        log_info_message("🔧 base_url is '/', so URL_PREFIX set to empty string")
    elif base_url and not base_url.startswith("/"):
        url_prefix = "/" + base_url
        log_info_message(f"🔧 base_url missing leading '/', fixed to: {url_prefix}")
    else:
        url_prefix = base_url
        log_info_message(f"🔧 base_url already starts with '/': {url_prefix}")

    app.config["URL_PREFIX"] = url_prefix
    log_info_message(f"🚀 Final URL_PREFIX set to: {url_prefix}")
