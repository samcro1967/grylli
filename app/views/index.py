from app.utils.locale import get_locale
from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("index_bp", __name__)

@bp.route("/")
@login_required
def index():
    return render_template("index.html")

from flask import jsonify
from flask_babel import gettext
from app import get_locale

@bp.route("/langcheck")
def langcheck():
    return jsonify({
        "locale": get_locale(),
        "translated": gettext("Welcome to Grylli")
    })

@bp.route("/checkme/")
def checkme():
    return "✅ Blueprint is correctly mounted"