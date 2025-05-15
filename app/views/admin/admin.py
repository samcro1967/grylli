from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.db import get_db

@bp.route('/users/edit/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    # TODO: Implement form handling to edit user details here
    return f"Edit user {user_id} - To be implemented"

@bp.route('/users/delete/<int:user_id>/', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User deleted.", "success")
    return redirect(url_for('admin.list_users'))
