import os

from flask import Blueprint, abort, flash, render_template, request
from flask_babel import _

from app.forms.admin_help_form import AdminHelpForm
from app.utils.logging import log_exception_with_traceback, log_info_message

admin_help = Blueprint("admin_help", __name__)


# ---------------------------------------------------------------------
# Admin help route
# ---------------------------------------------------------------------
@admin_help.route("/help", methods=["GET", "POST"])
def help_page():
    """
    Display the admin help form and validate FERRET_KEY before showing help content.
    """
    #  Hard block GET requests with parameters BEFORE form parsing
    if request.method == "GET" and request.args:
        abort(405)

    #  Only now instantiate form safely
    form = AdminHelpForm()

    try:
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if form.validate_on_submit():
            expected_key = os.environ.get("FERRET_KEY")
            if expected_key and form.ferret_key.data == expected_key:
                log_info_message(f"FERRET_KEY access granted from IP {client_ip}")
                return render_template("admin/help.html")

            flash(_("Invalid Ferret Key."), "error")
            log_info_message(f"FERRET_KEY access denied from IP {client_ip}")

        return render_template("admin/help_form.html", form=form)

    except Exception:
        log_exception_with_traceback("Unhandled error in /help route")
        flash(_("An internal error occurred. Please try again later."), "danger")
        return render_template("admin/help_form.html", form=form)
