"""
# ---------------------------------------------------------------------
# locale.py
# app/utils/locale.py
# Locale utility for determining user language preference.
# ---------------------------------------------------------------------
"""

from flask import current_app, request, session


def get_locale():
    """
    Return the user's preferred locale, falling back to the default language.

    Returns:
        Locale string (e.g., "en", "de").
    """
    supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()
    user_locale = request.cookies.get("user_locale")
    if user_locale in supported:
        return user_locale
