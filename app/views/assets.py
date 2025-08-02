# ------------------------------------------------------------------------------
# assets.py
# app/views/assets.py
#
# Routes for serving static assets like fonts or background patterns via Flask.
# ------------------------------------------------------------------------------

import os
from flask import Blueprint, send_from_directory, abort, render_template, Response, request
from app.config import AVAILABLE_FONTS, PROJECT_ROOT

bp = Blueprint("assets", __name__)


@bp.route("/fonts/<path:filename>", strict_slashes=False)
def serve_font(filename):
    base_dir = os.path.join(PROJECT_ROOT, "app", "assets", "fonts")
    full_path = os.path.abspath(os.path.join(base_dir, filename))

    if not os.path.commonpath([full_path, base_dir]) == base_dir:
        abort(403)

    file = os.path.basename(full_path)
    ALLOWED_EXTENSIONS = {'.woff2', '.woff', '.ttf'}
    if not any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        abort(403)

    directory = os.path.dirname(full_path)
    return send_from_directory(directory, file)


@bp.route("/fonts.css", strict_slashes=False)
def fonts_css():
    try:
        css = render_template(
            "static/css/_fonts.css.j2",
            fonts=AVAILABLE_FONTS,
            asset_base=request.script_root.rstrip("/") + "/assets/fonts"
        )
        return Response(css, mimetype="text/css")
    except Exception as e:
        return "CSS generation failed", 500
