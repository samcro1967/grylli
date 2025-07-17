# ---------------------------------------------------------------------
# pwa.py
# app/views/pwa.py
# ---------------------------------------------------------------------

from flask import Blueprint, jsonify, url_for

bp = Blueprint("pwa", __name__)


@bp.route("manifest.json", strict_slashes=True)
def manifest():
    return (
        jsonify(
            {
                "name": "Grylli",
                "short_name": "Grylli",
                "start_url": url_for("auth.login"),
                "display": "standalone",
                "background_color": "#1e293b",
                "theme_color": "#1e293b",
                "icons": [
                    {
                        "src": url_for("static", filename="icons/icon-192.png"),
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "any",
                    },
                    {
                        "src": url_for("static", filename="icons/icon-512.png"),
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any",
                    },
                ],
                "screenshots": [
                    {
                        "src": url_for("static", filename="screenshots/welcome-desktop.png"),
                        "sizes": "1280x800",
                        "type": "image/png",
                        "form_factor": "wide",
                    },
                    {
                        "src": url_for("static", filename="screenshots/welcome-mobile.png"),
                        "sizes": "390x844",
                        "type": "image/png",
                        "form_factor": "narrow",
                    },
                ],
            }
        ),
        200,
        {"Content-Type": "application/manifest+json"},
    )
