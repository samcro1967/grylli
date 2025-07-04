# ---------------------------------------------------------------------
# user_smtp.py
# app/views/user_smtp.py
# User SMTP configuration management views.
# ---------------------------------------------------------------------

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.forms.user_smtp_form import SmtpForm
from app.models import UserMailSettings, db
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("user_smtp", __name__, url_prefix="/email")


# ---------------------------------------------------------------------
# List SMTP Configs
# ---------------------------------------------------------------------
@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
def overview():
    """
    Display the list of SMTP configurations for the current user.
    Renders full layout for normal requests, partial for HTMX.
    """
    try:
        smtp_list = UserMailSettings.query.filter_by(user_id=current_user.id).all()
        log_info_message(f"User '{current_user.username}' viewed their SMTP config list.")

        template = (
            "user_smtp/list_smtp_partial.html"
            if request.headers.get("HX-Request")
            else "user_smtp/list_smtp_full.html"
        )
        return render_template(template, smtp_list=smtp_list)

    except Exception as e:
        log_exception_with_traceback("Error displaying SMTP config list", e)
        flash(_("Unable to load SMTP configurations."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Create SMTP Config
# ---------------------------------------------------------------------
@bp.route("create", methods=["GET", "POST"], strict_slashes=False)
@login_required
def create():
    form = SmtpForm()
    try:
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

            smtp.smtp_password = form.smtp_password.data or ""

            db.session.add(smtp)
            db.session.commit()

            log_info_message(
                f"User '{current_user.username}' created SMTP config '{smtp.label}' (ID={smtp.id})."
            )
            flash(_("SMTP destination created successfully."), "success")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "smtpListChanged"
                return response

            return redirect(url_for("user_smtp.overview"))

        template = (
            "user_smtp/create_smtp_partial.html"
            if request.headers.get("HX-Request")
            else "user_smtp/create_smtp_full.html"
        )
        return render_template(template, form=form)

    except Exception as e:
        log_exception_with_traceback("Error creating new SMTP config", e)
        flash(_("Error creating SMTP configuration."), "danger")
        return redirect(url_for("user_smtp.overview"))


# ---------------------------------------------------------------------
# Edit SMTP Config
# ---------------------------------------------------------------------
@bp.route("<int:smtp_id>/edit", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit(smtp_id):
    try:
        smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

        if request.method == "GET":
            form = SmtpForm()
            form.label.data = smtp.label
            form.smtp_host.data = smtp.smtp_host
            form.smtp_port.data = smtp.smtp_port
            form.smtp_username.data = smtp.smtp_username
            form.use_tls.data = smtp.use_tls
            form.enabled.data = smtp.enabled
            form.smtp_password.data = smtp.smtp_password
            log_info_message(
                f"User '{current_user.username}' opened edit form for SMTP config ID={smtp.id}."
            )
        else:
            form = SmtpForm(obj=smtp)

        if form.validate_on_submit():
            form.populate_obj(smtp)
            if form.smtp_password.data:
                smtp.smtp_password = form.smtp_password.data
            db.session.commit()
            log_info_message(
                f"User '{current_user.username}' updated SMTP config '{smtp.label}' (ID={smtp.id})."
            )
            flash(_("SMTP destination updated."), "success")

            # Determine if the request is an HTMX request
            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "smtpListChanged"
                return response

            return redirect(url_for("user_smtp.overview"))

        # Determine which template to use (full or partial) based on the request type
        template = (
            "user_smtp/edit_smtp_partial.html"  # Partial view for HTMX requests
            if request.headers.get("HX-Request")
            else "user_smtp/edit_smtp_full.html"  # Full view for regular requests
        )

        return render_template(template, form=form, smtp=smtp)

    except Exception as e:
        log_exception_with_traceback("Error editing SMTP config", e)
        flash(_("Failed to load or update SMTP config."), "danger")
        return redirect(url_for("user_smtp.overview"))


# ---------------------------------------------------------------------
# Delete SMTP Config
# ---------------------------------------------------------------------
@bp.route("<int:smtp_id>/delete", methods=["POST"], strict_slashes=False)
@login_required
def delete(smtp_id):
    try:
        smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()
        db.session.delete(smtp)
        db.session.commit()
        log_info_message(
            f"User '{current_user.username}' deleted SMTP config '{smtp.label}' (ID={smtp.id})."
        )
        flash(_("SMTP destination deleted."), "info")
    except Exception as e:
        log_exception_with_traceback("Error deleting SMTP config", e)
        flash(_("Error deleting SMTP configuration."), "danger")
    return redirect(url_for("user_smtp.overview"))


# ---------------------------------------------------------------------
# Send Test email using SMTP Config
# ---------------------------------------------------------------------
@bp.route("<int:smtp_id>/send-test", methods=["POST"], strict_slashes=False)
@login_required
def send_test(smtp_id):
    from app.services.smtp.email_utils import send_test_smtp

    try:
        smtp = UserMailSettings.query.filter_by(id=smtp_id, user_id=current_user.id).first_or_404()

        if send_test_smtp(current_user, smtp):
            log_info_message(
                f"User '{current_user.username}' successfully sent test email for SMTP config ID={smtp.id}."
            )
            flash(_("Test email sent successfully to your account email."), "success")
        else:
            log_info_message(
                f"User '{current_user.username}' failed to send test email for SMTP config ID={smtp.id}."
            )
            flash(_("Failed to send test email. Check SMTP settings."), "danger")

    except Exception as e:
        log_exception_with_traceback("Error sending SMTP test email", e)
        flash(_("Error sending test email."), "danger")

    return redirect(url_for("user_smtp.overview"))
