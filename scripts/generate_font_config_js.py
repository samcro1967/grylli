# scripts/generate_font_config_js.py

"""
generate_font_config_js.py
Generates app/static/js/font_config.js from config.py's AVAILABLE_FONTS.
"""

import os
import sys
from flask import Flask, render_template

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "app")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

# Ensure config.py is importable
sys.path.insert(0, APP_DIR)
from config import AVAILABLE_FONTS  # ✅ direct import

def generate_font_config():
    app = Flask(__name__, template_folder=TEMPLATES_DIR)

    # Inject values directly (no from_object)
    app.config["AVAILABLE_FONTS"] = AVAILABLE_FONTS
    app.config["BASE_URL"] = "/grylli"

    with app.app_context():
        js = render_template("static/js/font_config.js.j2", config=app.config)
        output_path = os.path.join(APP_DIR, "static", "js", "font_config.js")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"✅ Generated {output_path}")

if __name__ == "__main__":
    generate_font_config()
