# ---------------------------------------------------------------------
# about.py
# Blueprint for rendering the About page in Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template

# ---------------------------------------------------------------------
# Blueprint Configuration
# ---------------------------------------------------------------------

bp = Blueprint("about", __name__, url_prefix="/about")

# ---------------------------------------------------------------------
# Route: /about
# ---------------------------------------------------------------------

@bp.route("/about/", methods=["GET"])
def show_about():
    """
    Renders the About page, including version and GitHub info.

    Returns:
        str: Rendered HTML for the About page.
    """
    return render_template("about.html")
