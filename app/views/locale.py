# ---------------------------------------------------------------------
# locale.py
# app/views/locale.py
# Locale/translation switching blueprint and utility routes.
# ---------------------------------------------------------------------

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask_babel import _, gettext
from flask_login import current_user, login_required

from app.utils.locale import get_locale
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.utils.security import get_safe_redirect

bp = Blueprint("locale", __name__)


# ---------------------------------------------------------------------
# Locale set AJAX language route
# ---------------------------------------------------------------------
@bp.route("locale/set", methods=["POST"], strict_slashes=False)
def set_locale_post():
    """
    Handles the AJAX request for setting the user's locale, and redirects
    them back to the current page or the home page if the referrer is not
    set.
    """
    try:
        supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()
        locale_code = request.form.get("lang", "en")

        if locale_code not in supported:
            locale_code = "en"

        session["user_locale"] = locale_code
        session.modified = True
        log_info_message(
            f"Locale set via POST to '{locale_code}' (user: {current_user.username if current_user.is_authenticated else 'anonymous'})."
        )

        # Safe redirect: `request.referrer` validated via `get_safe_redirect()`
        return redirect(get_safe_redirect(request.referrer, fallback_endpoint="home.index"))
    except Exception as e:
        log_exception_with_traceback("Failed to set locale via POST", e)
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Locale set language route
# ---------------------------------------------------------------------
@bp.route("locale/set/<lang_code>", methods=["GET"], strict_slashes=False)
def set_language(lang_code):
    """
    Handles the GET request for setting the user's locale cookie, and redirects
    them back to the current page or the home page if the referrer is not
    set.
    """
    try:
        supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()
        default_lang = current_app.config.get("DEFAULT_LANGUAGE", "en")

        #  Sanitize input: enforce a strict language code pattern
        import re

        VALID_LANG_PATTERN = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")

        if lang_code not in supported or not VALID_LANG_PATTERN.match(lang_code.strip()):
            lang_code = default_lang

        lang_code = lang_code.strip()

        # Safe redirect URL derived from sanitized `request.referrer`
        redirect_url = get_safe_redirect(request.referrer, fallback_endpoint="home.index")
        resp = make_response(redirect(redirect_url))
        resp.set_cookie(
            "user_locale",
            lang_code,
            max_age=60 * 60 * 24 * 365,
            path="/",
            secure=current_app.config.get("SESSION_COOKIE_SECURE", False),
            samesite="Lax",
        )
        log_info_message(
            f"Access - {current_user.username if current_user.is_authenticated else 'anonymous'} - Locale set to '{lang_code}'"
        )
        return resp
    except Exception as e:
        log_exception_with_traceback("Failed to set locale cookie via GET", e)
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Locale language check route
# ---------------------------------------------------------------------
@bp.route("locale/langcheck", strict_slashes=False)
@login_required
def langcheck():
    """
    Debug route to verify current Babel language settings.
    Only accessible to logged-in admins.
    """
    try:
        if not current_user.is_admin:
            abort(403)

        lang = get_locale()
        log_info_message(f"Access - {current_user.username} - Locale Diagnostics")
        return jsonify({"manual_locale": lang, "babel_locale": str(gettext("Welcome to Grylli"))})
    except Exception as e:
        log_exception_with_traceback("Failed to check language locale", e)
        return jsonify({"error": _("Failed to determine locale.")}), 500
