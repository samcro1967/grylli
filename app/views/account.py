# ---------------------------------------------------------------------
# account.py
# Blueprint for managing user account settings
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.forms.account_form import AccountForm
from app.models import db, User
from app.utils.logging import log_info_message, log_error_message

bp = Blueprint("account", __name__, url_prefix="/account")

# ---------------------------------------------------------------------
# Route: Manage Account (view and update user account info)
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET", "POST"])
@login_required
def manage_account():
    form = AccountForm(obj=current_user)

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()

        if form.new_password.data:
            if not form.current_password.data:
                flash("Current password is required to change password.", "danger")
                return render_template("account/manage_account.html", form=form)

            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash("Current password is incorrect.", "danger")
                return render_template("account/manage_account.html", form=form)

            current_user.password_hash = generate_password_hash(form.new_password.data)

        # Update the fields
        current_user.username = username
        current_user.email = email

        try:
            db.session.commit()
            flash("Account updated successfully.", "success")
            log_info_message(f"User '{current_user.username}' updated their account.")
            return redirect(url_for("account.manage_account"))
        except Exception as e:
            db.session.rollback()
            log_error_message(f"Failed to update user {current_user.id}: {e}")
            flash(f"An error occurred while updating your account.", "danger")

    return render_template("account/manage_account.html", form=form)
