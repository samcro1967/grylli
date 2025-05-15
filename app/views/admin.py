from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.db import get_db
from app.forms.edit_user_form import EditUserForm

# Define Blueprint here — this is essential
bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/users/')
@login_required
def list_users():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    db = get_db()
    users = db.execute("SELECT id, username, email, role FROM users").fetchall()
    return render_template('admin/list_users.html', users=users)

@bp.route('/users/edit/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    
    db = get_db()
    user_row = db.execute("SELECT id, username, email, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_row is None:
        flash("User not found.", "danger")
        return redirect(url_for('admin.list_users'))
    
    form = EditUserForm()
    
    if request.method == "GET":
        # Pre-fill form fields
        form.username.data = user_row['username']
        form.email.data = user_row['email']
        form.role.data = user_row['role']

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        role = form.role.data.strip()
        password = form.new_password.data.strip()

        if password:
            password_hash = generate_password_hash(password)
            db.execute(
                "UPDATE users SET username = ?, email = ?, role = ?, password_hash = ? WHERE id = ?",
                (username, email, role, password_hash, user_id)
            )
        else:
            db.execute(
                "UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
                (username, email, role, user_id)
            )
        db.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for('admin.list_users'))

    return render_template('admin/edit_user.html', form=form, user_id=user_id)

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
