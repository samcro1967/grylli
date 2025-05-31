"""
# ---------------------------------------------------------------------
# user_smtp.py
# app/views/user_smtp.py
# User SMTP configuration management views.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required
from sqlalchemy import text

from app.forms.user_smtp_form import SmtpForm
from app.models import UserMailSettings, db
from app.services.encryption import decrypt

bp = Blueprint("user_smtp", __name__, url_prefix="/email")


# ---------------------------------------------------------------------
# List all SMTP configs for the current user
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET"])
@login_required
def index():
    smtp_list = UserMailSettings.query.filter_by(user_id=current_user.id).all()
    # In user_smtp.py
    return render_template("user_smtp/list_smtp.html", smtp_list=smtp_list)


# ---------------------------------------------------------------------
# Create a new SMTP config
# ---------------------------------------------------------------------
@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = SmtpForm()

    if form.validate_on_submit():
        smtp = UserMailSettings(
            user_id=current_user.id,
            label=form.label.data,
            smtp_host=form.smtp_host.data,
            smtp_port=form.smtp_port.data,
            smtp_username=form.smtp_username.data,
            use_tls=form.use_tls.data,
            enabled=form.enabled.data,
        )

        if form.smtp_password.data:
            smtp.smtp_password = form.smtp_password.data

        db.session.add(smtp)
        db.session.commit()
        flash(_("SMTP destination created successfully."), "success")
        return redirect(url_for("user_smtp.index"))

    return render_template("user_smtp/create_smtp.html", form=form)


# ---------------------------------------------------------------------
# Edit an existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/edit", methods=["GET", "POST"])
@login_required
def edit(smtp_id):
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

    if request.method == "GET":
        form = SmtpForm()
        form.label.data = smtp.label
        form.smtp_host.data = smtp.smtp_host
        form.smtp_port.data = smtp.smtp_port
        form.smtp_username.data = smtp.smtp_username
        form.use_tls.data = smtp.use_tls
        form.enabled.data = smtp.enabled
        form.smtp_password.data = smtp.smtp_password  # ✅ already decrypted
    else:
        form = SmtpForm(obj=smtp)

    if form.validate_on_submit():
        form.populate_obj(smtp)

        if form.smtp_password.data:  # re-encrypt only if field has a value
            smtp.smtp_password = form.smtp_password.data

        db.session.commit()
        flash(_("SMTP destination updated."), "success")
        return redirect(url_for("user_smtp.index"))

    return render_template("user_smtp/edit_smtp.html", form=form)


# ---------------------------------------------------------------------
# Delete an existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/delete", methods=["POST"])
@login_required
def delete(smtp_id):
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()
    db.session.delete(smtp)
    db.session.commit()
    flash(_("SMTP destination deleted."), "info")
    return redirect(url_for("user_smtp.index"))


# ---------------------------------------------------------------------
# Send test email for an SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/send-test", methods=["POST"])
@login_required
def send_test(smtp_id):
    from app.services.smtp.email_utils import send_test_smtp

    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

    try:
        if send_test_smtp(current_user, smtp):
            flash(_("Test email sent successfully to your account email."), "success")
        else:
            flash(_("Failed to send test email. Check SMTP settings."), "danger")
    except Exception as e:
        flash(f"Error sending test email: {e}", "danger")

    return redirect(url_for("user_smtp.index"))
