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

from app.forms.user_smtp_form import SmtpForm
from app.models import UserMailSettings, db
from app.services.encryption import decrypt
from app.utils.logging import log_error_message, log_info_message

bp = Blueprint("user_smtp", __name__, url_prefix="/email")


# ---------------------------------------------------------------------
# List all SMTP configs for the current user
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET"])
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
    log_info_message(f"User '{current_user.username}' viewed their SMTP config list.")
    return render_template("user_smtp/list_smtp.html", smtp_list=smtp_list)


# ---------------------------------------------------------------------
# Create a new SMTP config
# ---------------------------------------------------------------------
@bp.route("/create", methods=["GET", "POST"])
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

        if form.smtp_password.data:
            smtp.smtp_password = form.smtp_password.data

        db.session.add(smtp)
        db.session.commit()
        flash(_("SMTP destination created successfully."), "success")
        log_info_message(
            f"User '{current_user.username}' created SMTP config '{smtp.label}' (ID={smtp.id})."
        )
        return redirect(url_for("user_smtp.index"))

    return render_template("user_smtp/create_smtp.html", form=form)


# ---------------------------------------------------------------------
# Edit an existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/edit", methods=["GET", "POST"])
@login_required
def edit(smtp_id):
    """
    Edit an existing SMTP configuration for the current user.

    Validates a form and updates an existing SMTP configuration based on the
    provided details. Logs an informational message indicating the user
    has edited an existing SMTP configuration and redirects to the list of
    SMTP configurations.

    Args:
        smtp_id: The ID of the SMTP configuration to edit.

    Returns:
        Rendered template displaying the form for editing an existing SMTP
        configuration if the form is invalid, or redirects to the list of
        SMTP configurations on success.
    """
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
        log_info_message(
            f"User '{current_user.username}' opened edit form for SMTP config ID={smtp.id}."
        )
    else:
        form = SmtpForm(obj=smtp)

    if form.validate_on_submit():
        form.populate_obj(smtp)

        if form.smtp_password.data:  # re-encrypt only if field has a value
            smtp.smtp_password = form.smtp_password.data

        db.session.commit()
        flash(_("SMTP destination updated."), "success")
        log_info_message(
            f"User '{current_user.username}' updated SMTP config '{smtp.label}' (ID={smtp.id})."
        )
        return redirect(url_for("user_smtp.index"))

    return render_template("user_smtp/edit_smtp.html", form=form)


# ---------------------------------------------------------------------
# Delete an existing SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/delete", methods=["POST"])
@login_required
def delete(smtp_id):
    """
    Delete an existing SMTP configuration for the current user.

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
    flash(_("SMTP destination deleted."), "info")
    log_info_message(
        f"User '{current_user.username}' deleted SMTP config '{smtp.label}' (ID={smtp.id})."
    )
    return redirect(url_for("user_smtp.index"))


# ---------------------------------------------------------------------
# Send test email for an SMTP config
# ---------------------------------------------------------------------
@bp.route("/<int:smtp_id>/send-test", methods=["POST"])
@login_required
def send_test(smtp_id):
    """
    Send a test email using the specified SMTP configuration.

    Sends a test email using the Apprise SMTP service to the logged-in user.
    Logs an informational message indicating the user has sent a test email,
    or logs an error message if the email fails. Redirects to the list of SMTP
    configurations on completion.

    Args:
        smtp_id: The ID of the SMTP configuration to send the test email with.

    Returns:
        Redirect to the list of SMTP configurations.
    """
    from app.services.smtp.email_utils import send_test_smtp

    smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

    try:
        if send_test_smtp(current_user, smtp):
            flash(_("Test email sent successfully to your account email."), "success")
            log_info_message(
                f"User '{current_user.username}' successfully sent test email for SMTP config ID={smtp.id}."
            )
        else:
            flash(_("Failed to send test email. Check SMTP settings."), "danger")
            log_info_message(
                f"User '{current_user.username}' failed to send test email for SMTP config ID={smtp.id}."
            )
    except Exception as e:
        flash(f"Error sending test email: {e}", "danger")
        log_error_message(
            f"Exception during SMTP test for user '{current_user.username}' on config ID={smtp.id}: {e}"
        )

    return redirect(url_for("user_smtp.index"))
