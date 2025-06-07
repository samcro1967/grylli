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
from app.utils.logging import log_info_message

bp = Blueprint("smtp_bp", __name__)


# ---------------------------------------------------------------------
# List all SMTP configs
# ---------------------------------------------------------------------
@bp.route("/smtp")
@login_required
def index():
    """
    Display a list of all SMTP configurations for the current user.

    Queries the database for SMTP configurations associated with the
    logged-in user and renders them in the 'list_smtp.html' template.
    Logs an informational message indicating the user has viewed their
    SMTP configurations.

    Returns:
        Rendered template displaying the user's SMTP configurations.
    """

    smtp_list = UserMailSettings.query.filter_by(user_id=current_user.id).all()
    log_info_message(f"User '{current_user.username}' viewed their SMTP configurations.")
    return render_template("user_smtp/list_smtp.html", smtp=smtp)


# ---------------------------------------------------------------------
# Create new SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Create a new SMTP configuration for the current user.

    Validates a form and creates a new SMTP configuration based on the
    provided details. Logs an informational message indicating the user
    has created a new SMTP configuration and redirects to the list of SMTP
    configurations.

    Returns:
        Rendered template displaying the form for creating a new SMTP
        configuration if the form is invalid, or redirects to the list of
        SMTP configurations on success.
    """
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
        log_info_message(
            f"User '{current_user.username}' created new SMTP config '{smtp.label}' (ID={smtp.id})."
        )
        flash(_("SMTP destination created successfully."), "success")
        return redirect(url_for("smtp_bp.index"))

    return render_template("user_smtp/create_smtp.html", form=form)


# ---------------------------------------------------------------------
# Edit existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/edit", methods=["GET", "POST"])
@login_required
def edit(smtp_id):
    """
    Edit an existing SMTP configuration.

    Validates a form and updates an existing SMTP configuration in the
    database. Logs an informational message indicating the user has edited
    an existing SMTP configuration and redirects to the list of SMTP
    configurations.

    Args:
        smtp_id: The ID of the SMTP configuration to edit.

    Returns:
        Rendered template displaying the form for editing an existing SMTP
        configuration if the form is invalid, or redirects to the list of
        SMTP configurations on success.
    """
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
        log_info_message(
            f"User '{current_user.username}' edited SMTP config '{smtp.label}' (ID={smtp.id})."
        )
        flash(_("SMTP destination updated."), "success")
        return redirect(url_for("smtp_bp.index"))

    return render_template("smtp/edit_smtp.html", form=form)


# ---------------------------------------------------------------------
# Delete SMTP config
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/delete", methods=["POST"])
@login_required
def delete(smtp_id):
    """
    Delete an existing SMTP configuration.

    Deletes an existing SMTP configuration from the database. Logs an
    informational message indicating the user has deleted an existing
    SMTP configuration and redirects to the list of SMTP configurations.

    Args:
        smtp_id: The ID of the SMTP configuration to delete.

    Returns:
        Redirect to the list of SMTP configurations.
    """
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()
    db.session.delete(smtp)
    db.session.commit()
    log_info_message(
        f"User '{current_user.username}' deleted SMTP config '{smtp.label}' (ID={smtp.id})."
    )
    flash(_("SMTP destination deleted."), "info")
    return redirect(url_for("smtp_bp.index"))


# ---------------------------------------------------------------------
# Send Test Email
# ---------------------------------------------------------------------
@bp.route("/smtp/<int:smtp_id>/send-test", methods=["POST"])
@login_required
def send_test(smtp_id):
    """
    Send a test email for the specified SMTP configuration.

    Uses the Apprise SMTP service to send a test email to the logged-in user.
    Logs an informational message indicating the user has sent a test email,
    or logs an error message if the email fails. Redirects to the list of SMTP
    configurations on completion.

    Args:
        smtp_id: The ID of the SMTP configuration to send the test email with.

    Returns:
        Redirect to the list of SMTP configurations.
    """
    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

    try:
        if send_test_smtp(current_user, smtp):
            log_info_message(
                f"User '{current_user.username}' sent test email using SMTP config ID={smtp.id}."
            )
            flash(_("Test email sent successfully to your account email."), "success")
        else:
            log_info_message(
                f"User '{current_user.username}' failed test email using SMTP config ID={smtp.id}."
            )
            flash(_("Failed to send test email. Check SMTP settings."), "danger")
    except Exception as e:
        log_info_message(
            f"User '{current_user.username}' encountered error sending test email via SMTP config ID={smtp.id}: {str(e)}"
        )
        flash("Error sending test email: " + str(e), "danger")

    return redirect(url_for("smtp_bp.index"))
