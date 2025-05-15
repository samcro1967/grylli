# ---------------------------------------------------------------------
# admin.py
# Admin user management views for Grylli
# ---------------------------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.forms.edit_user_form import EditUserForm
from app.models import db, User
from app.utils.logging import log_info_message, log_error_message

from app.models import SystemConfig
from app.services.encryption import decrypt

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ---------------------------------------------------------------------
# View: List all users
# ---------------------------------------------------------------------
@bp.route('/users/')
@login_required
def list_users():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    users = User.query.with_entities(User.id, User.username, User.email, User.role).all()
    return render_template('admin/list_users.html', users=users)

# ---------------------------------------------------------------------
# View: Edit a specific user
# ---------------------------------------------------------------------
@bp.route('/users/edit/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.list_users'))

    form = EditUserForm()

    if request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role

    if form.validate_on_submit():
        user.username = form.username.data.strip()
        user.email = form.email.data.strip()
        user.role = form.role.data.strip()

        if form.new_password.data:
            user.password_hash = generate_password_hash(form.new_password.data.strip())

        try:
            db.session.commit()
            flash("User updated successfully.", "success")
            log_info_message(f"Admin '{current_user.username}' updated user '{user.username}'.")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the user.", "danger")
            log_error_message(f"Failed to update user {user_id}: {e}")

    return render_template('admin/edit_user.html', form=form, user_id=user_id)

# ---------------------------------------------------------------------
# View: Delete a specific user
# ---------------------------------------------------------------------
@bp.route('/users/delete/<int:user_id>/', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.list_users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
        log_info_message(f"Admin '{current_user.username}' deleted user '{user.username}'.")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the user.", "danger")
        log_error_message(f"Failed to delete user {user_id}: {e}")

    return redirect(url_for('admin.list_users'))

# ---------------------------------------------------------------------
# System:
# ---------------------------------------------------------------------
@bp.route('/system/')
@login_required
def view_system_config():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    settings = SystemConfig.query.order_by(SystemConfig.key).all()

    for setting in settings:
        if setting.is_sensitive:
            try:
                setting.value = decrypt(setting.value)
            except Exception:
                setting.value = "[decryption error]"

    return render_template("admin/system_config.html", settings=settings)
