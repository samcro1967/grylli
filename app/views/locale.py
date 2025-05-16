from flask import Blueprint, request, redirect, url_for, make_response

bp = Blueprint("locale", __name__)

@bp.route("/set", methods=["POST"])
def set_locale_post():
    locale_code = request.form.get("lang")
    response = make_response(redirect(request.referrer or url_for("index_bp.index")))
    response.set_cookie("user_locale", locale_code)
    return response
