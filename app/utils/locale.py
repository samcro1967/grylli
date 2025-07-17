# ---------------------------------------------------------------------
# locale_utils.py
# app/utils/locale_utils.py
# Locale resolution helper with fallback chain and logging.
# ---------------------------------------------------------------------

from flask import current_app, request, session

from app.utils.logging import log_debug_message, log_exception_with_traceback, log_info_message


def get_locale():
    """
    Return the user's preferred locale, falling back to the default language.

    Priority:
        1. Session (user_locale)
        2. Cookie (user_locale)
        3. Accept-Language header
        4. Default app language
    """
    try:
        supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()

        user_locale = session.get("user_locale")
        if user_locale in supported:
            return user_locale  # Silent

        user_locale = request.cookies.get("user_locale")
        if user_locale in supported:
            return user_locale  # Silent

        accepted = request.accept_languages.best_match(supported)
        if accepted:
            return accepted  # Silent

        default_locale = current_app.config.get("DEFAULT_LANGUAGE", "en")
        return default_locale

    except Exception as e:
        log_exception_with_traceback("Error resolving locale", e)
        return "en"
