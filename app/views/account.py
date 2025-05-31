"""
# ---------------------------------------------------------------------
# account.py
# app/views/account.py
# Blueprint for managing user account settings and translations info.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_babel import _  # Added for translation support
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import GITHUB_URL
from app.forms.account_form import AccountForm
from app.models import User, db
from app.utils.logging import log_error_message, log_info_message

bp = Blueprint("account", __name__)


# ---------------------------------------------------------------------
# Route: Manage Account (view and update user account info)
# ---------------------------------------------------------------------
@bp.route("/account", methods=["GET", "POST"])
@login_required
def manage_account():
    """
    Route: Manage Account (view and update user account info)

    This route renders the `manage_account.html` template, displaying the user's current
    account information. The form is pre-populated with the current user's data. If the user
    submits the form, the route updates the user's account information in the database
    and redirects the user to the same page with a success message. If there is an error,
    the route redirects the user to the same page with an error message.

    The route requires the user to be logged in and will redirect an anonymous user to the
    login page.

    :param: None
    :return: render_template("account/manage_account.html", form=form)
    """
    form = AccountForm(obj=current_user)

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()

        if form.new_password.data:
            if not form.current_password.data:
                flash(_("Current password is required to change password."), "danger")
                return render_template("account/manage_account.html", form=form)

            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash(_("Current password is incorrect."), "danger")
                return render_template("account/manage_account.html", form=form)

            current_user.password_hash = generate_password_hash(form.new_password.data)

        # Update the fields
        current_user.username = username
        current_user.email = email

        try:
            db.session.commit()
            flash(_("Account updated successfully."), "success")
            log_info_message(f"User '{current_user.username}' updated their account.")
            return redirect(url_for("account.manage_account"))
        except Exception as e:
            db.session.rollback()
            log_error_message(f"Failed to update user {current_user.id}: {e}")
            flash(_("An error occurred while updating your account."), "danger")

    return render_template("account/manage_account.html", form=form)


# ---------------------------------------------------------------------
# Route: Translations Info Page
# ---------------------------------------------------------------------
@bp.route("/account/translations")
@login_required
def translations_info():
    """
    Route: Display information about Grylli translations
    """
    return render_template("account/translations.html", github_url=GITHUB_URL)
