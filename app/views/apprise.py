"""
# ---------------------------------------------------------------------
# apprise.py
# app/views/apprise.py
# Blueprint for Apprise destination configuration and test routes.
# ---------------------------------------------------------------------
"""

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _  # ✅ For translations
from flask_login import current_user, login_required

from app.forms.apprise_form import AppriseForm
from app.models import AppriseURL, db

# from app.services.apprise import send_test_apprise_notification
from app.services.apprise_utils import send_test_apprise_notification
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("apprise_routes", __name__)


# ---------------------------------------------------------------------
# Apprise test route
# ---------------------------------------------------------------------
@bp.route("/<int:id>/test", methods=["POST"])
@login_required
def test_apprise(id):
    """
    Sends a test notification for the specified Apprise destination.

    Retrieves the AppriseURL object by its ID, then attempts to send a test
    notification using the URL associated with that object. Displays a success
    message if the notification is sent successfully, or an error message if
    it fails.

    Args:
        id (int): The ID of the AppriseURL object to test.

    Returns:
        A redirect to the Apprise configuration page.
    """

    apprise = db.session.execute(db.select(AppriseURL).filter_by(id=id)).scalar_one_or_none()

    if apprise is None:
        abort(404)

    try:
        success, response = send_test_apprise_notification(apprise.url)
        if success:
            flash(_("🧪 Test notification sent successfully!"), "success")
            log_info_message(
                f"Apprise test succeeded for user {current_user.username}: ID={apprise.id}, label='{apprise.label}'"
            )
        else:
            flash(_("🧪 Failed to send test notification: ") + response, "danger")
            log_info_message(
                f"Apprise test failed for user {current_user.username}: ID={apprise.id}, label='{apprise.label}', reason='{response}'"
            )
    except Exception as e:
        log_exception_with_traceback("Apprise test failed", e)
        flash(_("🧪 Error sending test notification."), "danger")

    return redirect(url_for("apprise_routes.config"))


# ---------------------------------------------------------------------
# Apprise create toute
# ---------------------------------------------------------------------
@bp.route("/create/", methods=["GET", "POST"])
@login_required
def create_apprise():
    """
    Handle creation of a new Apprise destination.
    """
    form = AppriseForm()

    if form.validate_on_submit():
        apprise = AppriseURL(
            label=form.label.data.strip(),
            url=form.url.data.strip(),
            enabled=form.enabled.data,
            user_id=current_user.id,
            created_at=datetime.now(timezone.utc),
        )
        try:
            db.session.add(apprise)
            db.session.commit()
            flash(_("Apprise destination created successfully."), "success")
            log_info_message(f"Apprise created by {current_user.username}: {apprise.label}")

            if request.headers.get("HX-Request"):
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "appriseListChanged"
                return response

            return redirect(url_for("apprise_routes.config"))

        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Failed to create Apprise destination", e)
            flash(_("Failed to create Apprise destination."), "danger")

    template = "apprise/create_apprise_partial.html" if request.headers.get("HX-Request") else "apprise/create_apprise_full.html"
    return render_template(template, form=form)


# ---------------------------------------------------------------------
# Apprise list view route
# ---------------------------------------------------------------------
@bp.route("/config")
@login_required
def config():
    """
    Displays the Apprise configuration page with full or partial rendering
    depending on HTMX headers.
    """
    try:
        apprise_urls = (
            AppriseURL.query.filter_by(user_id=current_user.id)
            .order_by(AppriseURL.created_at.desc())
            .all()
        )
        template = (
            "apprise/list_apprise_partial.html"
            if request.headers.get("HX-Request")
            else "apprise/list_apprise_full.html"
        )
        return render_template(template, destinations=apprise_urls)

    except Exception as e:
        log_exception_with_traceback("Failed to load Apprise configuration", e)
        flash(_("Failed to load Apprise destinations."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Apprise edit route
# ---------------------------------------------------------------------
@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_apprise(id):
    """
    Edits an existing Apprise destination.

    GET: Renders the edit_apprise.html template with an AppriseForm instance
    populated with the destination's data.

    POST: Validates the submitted form data, updates the destination with the
    provided data, and commits the changes to the database. If the update is
    successful, displays a success message and redirects to the Apprise
    configuration page. If the update fails, re-renders the template with the
    form data.

    Returns:
        A rendered template (edit_apprise.html) with the populated form (GET),
        or a redirect to the Apprise configuration page (POST).
    """
    apprise = db.session.execute(
        db.select(AppriseURL).filter_by(id=id, user_id=current_user.id)
    ).scalar_one_or_none()

    if not apprise:
        abort(404)

    form = AppriseForm(obj=apprise)

    if form.validate_on_submit():
        apprise.label = form.label.data.strip()
        apprise.url = form.url.data.strip()
        apprise.enabled = form.enabled.data
        try:
            db.session.commit()
            log_info_message(
                f"Apprise updated by {current_user.username}: ID={apprise.id}, label='{apprise.label}'"
            )
            flash(_("Apprise destination updated successfully."), "success")
            return redirect(url_for("apprise_routes.config"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback(f"Failed to update Apprise ID={apprise.id}", e)
            flash(_("Failed to update Apprise destination."), "danger")

    return render_template("apprise/edit_apprise.html", form=form, apprise=apprise)


# ---------------------------------------------------------------------
# Apprise delete route
# ---------------------------------------------------------------------
@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_apprise(id):
    """
    Deletes an Apprise destination.

    Args:
        id (int): The ID of the AppriseURL object to delete.

    Returns:
        A redirect to the Apprise configuration page.
    """
    apprise = db.session.execute(
        db.select(AppriseURL).filter_by(id=id, user_id=current_user.id)
    ).scalar_one_or_none()

    if not apprise:
        abort(404)

    try:
        db.session.delete(apprise)
        db.session.commit()
        log_info_message(
            f"Apprise deleted by {current_user.username}: ID={apprise.id}, label='{apprise.label}'"
        )
        flash(_("Apprise destination deleted."), "success")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback(f"Failed to delete Apprise ID={apprise.id}", e)
        flash(_("Failed to delete Apprise destination."), "danger")

    return redirect(url_for("apprise_routes.config"))
