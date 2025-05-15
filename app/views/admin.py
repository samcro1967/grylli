from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/users/')
@login_required
def list_users():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    db = get_db()
    users = db.execute("SELECT id, username, email, role FROM users").fetchall()
    return render_template('admin/list_users.html', users=users)
