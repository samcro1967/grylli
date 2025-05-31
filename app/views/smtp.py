"""
# ---------------------------------------------------------------------
# smtp.py
# app/views/smtp.py
# Views for managing multiple SMTP destinations for Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.forms.smtp_forms import SmtpForm
from app.models import User, UserMailSettings, db
from app.services.smtp.email_utils import send_test_smtp, validate_smtp_connection

bp = Blueprint("smtp_bp", __name__)


# ---------------------------------------------------------------------
# List all SMTP configs
# ---------------------------------------------------------------------
@bp.route("/smtp")
@login_required
def index():
    smtp_list = UserMailSettings.query.filter_by(user_id=current_user.id).all()
    return render_template("user_smtp/list_smtp.html", smtp=smtp)


# ---------------------------------------------------------------------
# Create new SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/create", methods=["GET", "POST"])
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

        if form.smtp_password.data and form.smtp_password.data != "********":
            smtp.smtp_password = form.smtp_password.data

        db.session.add(smtp)
        db.session.commit()
        flash(_("SMTP destination created successfully."), "success")
        return redirect(url_for("smtp_bp.index"))

    return render_template("user_smtp/create_smtp.html", form=form)


# ---------------------------------------------------------------------
# Edit existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/edit", methods=["GET", "POST"])
@login_required
def edit(smtp_id):
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()
    form = SmtpForm(obj=smtp)

    if request.method == "POST" and form.validate_on_submit():
        smtp.label = form.label.data
        smtp.smtp_host = form.smtp_host.data
        smtp.smtp_port = form.smtp_port.data
        smtp.smtp_username = form.smtp_username.data
        smtp.use_tls = form.use_tls.data
        smtp.enabled = form.enabled.data

        if form.smtp_password.data:
            smtp.smtp_password = form.smtp_password.data  # only update if provided

        db.session.commit()
        flash(_("SMTP destination updated."), "success")
        return redirect(url_for("smtp_bp.index"))

    return render_template("smtp/edit_smtp.html", form=form)


# ---------------------------------------------------------------------
# Delete SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/delete", methods=["POST"])
@login_required
def delete(smtp_id):
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()
    db.session.delete(smtp)
    db.session.commit()
    flash(_("SMTP destination deleted."), "info")
    return redirect(url_for("smtp_bp.index"))


# ---------------------------------------------------------------------
# Send Test Email
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/send-test", methods=["POST"])
@login_required
def send_test(smtp_id):
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

    try:
        if send_test_smtp(current_user, smtp):
            flash(_("Test email sent successfully to your account email."), "success")
        else:
            flash(_("Failed to send test email. Check SMTP settings."), "danger")
    except Exception as e:
        flash("Error sending test email: " + str(e), "danger")

    return redirect(url_for("smtp_bp.index"))
