# scripts/generate_fonts_css.py

import os
from flask import render_template

def generate_fonts_css(app):
    """
    Generate fonts.css with the correct BASE_URL from Flask app config.
    """
    with app.app_context():
        base_url = app.config.get("BASE_URL", "")
        css = render_template("static/css/_fonts.css.j2", base_url=base_url)
        output_path = os.path.join(app.root_path, "static", "css", "fonts.css")
        with open(output_path, "w") as f:
            f.write(css)
        print(f"✅ fonts.css written to {output_path}")
