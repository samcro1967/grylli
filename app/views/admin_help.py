"""
app/views/admin_help.py
View logic for the admin help page, protected by FERRET_KEY authentication.
"""

import os

from flask import Blueprint, current_app, flash, render_template, request

from app.forms.admin_help_form import AdminHelpForm
from app.models import SystemConfig
from app.utils.logging import log_info_message

admin_help = Blueprint("admin_help", __name__)


# ---------------------------------------------------------------------
# Admin help route
# ---------------------------------------------------------------------
@admin_help.route("/help", methods=["GET", "POST"])
def help_page():
    """
    Display the admin help form and validate FERRET_KEY before showing help content.
    """
    form = AdminHelpForm()

    # 🔐 Hard block GET requests with parameters
    if request.method == "GET" and request.args:
        abort(405)  # Method Not Allowed

    if form.validate_on_submit():
        expected_key = os.environ.get("FERRET_KEY")
        if expected_key and form.ferret_key.data == expected_key:
            log_info_message(f"FERRET_KEY access granted from IP {client_ip}")
            return render_template("admin/help.html")

        flash("Invalid Ferret Key.", "error")
        log_info_message(f"FERRET_KEY access denied from IP {client_ip}")

    return render_template("admin/help_form.html", form=form)
