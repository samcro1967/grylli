from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.forms.account_form import AccountForm
from app.db import get_db
from app.models import User

bp = Blueprint("account", __name__, url_prefix="/account")

@bp.route("/", methods=["GET", "POST"])
@login_required
def manage_account():
    form = AccountForm(obj=current_user)

    if form.validate_on_submit():
        db = get_db()

        # Update username and email
        username = form.username.data.strip()
        email = form.email.data.strip()

        # If changing password, verify current password
        if form.new_password.data:
            if not form.current_password.data:
                flash("Current password is required to change password.", "danger")
                return render_template("account/manage_account.html", form=form)

            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash("Current password is incorrect.", "danger")
                return render_template("account/manage_account.html", form=form)

            new_password_hash = generate_password_hash(form.new_password.data)
        else:
            new_password_hash = None

        try:
            if new_password_hash:
                db.execute(
                    "UPDATE users SET username=?, email=?, password_hash=? WHERE id=?",
                    (username, email, new_password_hash, current_user.id)
                )
            else:
                db.execute(
                    "UPDATE users SET username=?, email=? WHERE id=?",
                    (username, email, current_user.id)
                )
            db.commit()
            flash("Account updated successfully.", "success")

            # Optionally, update current_user properties here or require re-login

            return redirect(url_for("account.manage_account"))
        except Exception as e:
            flash("Error updating account: " + str(e), "danger")

    return render_template("account/manage_account.html", form=form)
