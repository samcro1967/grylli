"""
# ---------------------------------------------------------------------
# locale.py
# app/views/locale.py
# Locale/translation switching blueprint and utility routes.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, abort, current_app, jsonify, make_response, redirect, request, url_for
from flask_babel import gettext
from flask_login import current_user, login_required

from app.utils.locale import get_locale
from app.utils.logging import log_info_message

bp = Blueprint("locale", __name__)


@bp.route("/locale/set", methods=["POST"])
def set_locale_post():
    """
    Handles the AJAX request for setting the user's locale, and redirects
    them back to the current page or the home page if the referrer is not
    set.

    :param lang: The language code to set the user's locale to.
    :type lang: str
    """
    from flask import current_app, redirect, request, session, url_for

    supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()
    locale_code = request.form.get("lang", "en")

    if locale_code not in supported:
        locale_code = "en"

    # Set only the key, never reassign session directly
    session["user_locale"] = locale_code
    session.modified = True  # Explicitly mark the session as changed

    # Redirect back to the current page or home
    return redirect(request.referrer or url_for("index.index"))


@bp.route("/locale/set/<lang_code>", methods=["GET"])
def set_language(lang_code):
    supported = current_app.config.get("SUPPORTED_LANGUAGES", {}).keys()
    if lang_code not in supported:
        lang_code = current_app.config.get("DEFAULT_LANGUAGE", "en")
    resp = make_response(redirect(request.referrer or url_for("index.index")))
    resp.set_cookie(
        "user_locale",
        lang_code,
        max_age=60 * 60 * 24 * 365,  # 1 year
        path="/",  # VERY IMPORTANT
        secure=False,  # True only if HTTPS, otherwise False
        samesite="Lax",  # Default for most, but you can omit or set "Lax"
    )
    return resp


@bp.route("/locale/langcheck")
@login_required
def langcheck():
    """Debug route to verify current Babel language settings."""
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

    lang = get_locale()

    log_info_message("✅ log_info_message executed in /logtest route.")

    return jsonify({"manual_locale": lang, "babel_locale": str(gettext("Welcome to Grylli"))})
