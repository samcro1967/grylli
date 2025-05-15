# ---------------------------------------------------------------------
# index.py
# Root landing page view for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template

bp = Blueprint("index", __name__)

@bp.route("/")
def index():
    """
    Default landing page for Grylli.
    """
    return render_template("index.html")
