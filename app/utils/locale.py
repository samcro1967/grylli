from flask import current_app, request, session


def get_locale():
    """
    Return the user's preferred locale, falling back to the default language.

    Priority:
        1. Session (user_locale)
        2. Cookie (user_locale)
        3. Accept-Language header
        4. Default app language
    """
    supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()

    # 1. Check session first
    user_locale = session.get("user_locale")
    if user_locale in supported:
        return user_locale

    # 2. Check cookie next
    user_locale = request.cookies.get("user_locale")
    if user_locale in supported:
        return user_locale

    # 3. Use Accept-Language header
    accepted = request.accept_languages.best_match(supported)
    if accepted:
        return accepted

    # 4. Fallback to default
    return current_app.config.get("DEFAULT_LANGUAGE", "en")
