"""
app/views/admin_help.py
View logic for the admin help page, protected by FERRET_KEY authentication.
"""

from flask import Blueprint, current_app, flash, render_template

from app.forms.admin_help_form import AdminHelpForm
from app.models import SystemConfig

admin_help = Blueprint("admin_help", __name__)


@admin_help.route("/help", methods=["GET", "POST"])
def help_page():
    """
    Display the admin help form and validate FERRET_KEY before showing help content.
    """
    form = AdminHelpForm()
    if form.validate_on_submit():
        ferret_row = SystemConfig.query.filter_by(key="FERRET_KEY").first()
        if ferret_row and form.ferret_key.data == ferret_row.value:
            return render_template("admin/help.html")
        flash("Invalid Ferret Key.", "error")
    return render_template("admin/help_form.html", form=form)
