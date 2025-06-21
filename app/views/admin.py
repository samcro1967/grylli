"""
# ---------------------------------------------------------------------
# admin.py
# app/views/admin.py
# Admin landing page view and blueprint for Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required

bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------
# Admin landing page
# ---------------------------------------------------------------------
@bp.route("/admin/")
@login_required
@admin_required
def admin_landing():
    """
    Admin landing page view.
    This view is accessible only to admin users.
    The page displays a simple heading and a link to the user management page.
    """

    return render_template("admin/index.html")


# ---------------------------------------------------------------------
# Admin change user role
# ---------------------------------------------------------------------
@bp.route("/admin/users/role/<int:user_id>", methods=["POST"])
@admin_required
def change_user_role(user_id):
    """
    Update the role of an existing user.

    This view is accessible only to admin users.
    The view expects a POST request with a "role" parameter containing either "user" or "admin".
    The user's role is updated in the database and a flash message is displayed.
    The role change is also logged.
    """
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")

    # Validate the new role
    if new_role not in ["user", "admin"]:
        flash(_("Invalid role."), "danger")
    # Update the user's role
    else:
        old_role = user.role
        user.role = new_role

        try:
            db.session.commit()
            flash(_(f"Role updated for {user.username}."), "success")
            log_info_message(
                f"Admin '{current_user.username}' changed role for user '{user.username}' "
                f"from '{old_role}' to '{new_role}'."
            )
        except Exception as e:
            db.session.rollback()
            flash(_("Failed to update user role."), "danger")
            log_exception_with_traceback(f"Error updating role for user ID={user_id}")

    return redirect(url_for("users.list_users"))
