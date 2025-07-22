# ------------------------------------------------------------------------------
# assets.py
# app/views/assets.py
#
# Routes for serving static assets like fonts or background patterns via Flask.
# ------------------------------------------------------------------------------

import os
from flask import Blueprint, send_from_directory, abort, render_template, Response
from app.config import AVAILABLE_FONTS

bp = Blueprint("assets", __name__)


@bp.route("/fonts/<path:filename>", strict_slashes=False)
def serve_font(filename):
    """
    Serve font files from node_modules/@fontsource/ safely.
    """
    base_dir = os.path.abspath(os.path.join("app", "assets", "fonts"))
    full_path = os.path.abspath(os.path.join(base_dir, filename))

    # Prevent path traversal
    if not full_path.startswith(base_dir):
        abort(403)

    directory = os.path.dirname(full_path)
    file = os.path.basename(full_path)

    return send_from_directory(directory, file)

@bp.route("/fonts.css", strict_slashes=False)
def fonts_css():
    """Serve dynamically generated @font-face CSS from AVAILABLE_FONTS."""
    from app.config import AVAILABLE_FONTS

    css = render_template("static/css/_fonts.css.j2", config={
        "AVAILABLE_FONTS": AVAILABLE_FONTS,
        "BASE_URL": "/grylli",  # or current_app.config["BASE_URL"]
    })
    return Response(css, mimetype="text/css")
