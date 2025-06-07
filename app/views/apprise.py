"""
# ---------------------------------------------------------------------
# apprise.py
# app/views/apprise.py
# Blueprint for Apprise destination configuration and test routes.
# ---------------------------------------------------------------------
"""

from datetime import datetime

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

    apprise = AppriseURL.query.get_or_404(id)

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
    Creates a new Apprise destination.

    GET: Renders the create_apprise.html template with an empty AppriseForm
    instance. The form is populated with data when the user submits it.

    POST: Validates the submitted form data, creates a new AppriseURL object
    with the provided data, and adds it to the database. If the creation is
    successful, displays a success message and logs the creation, then
    redirects to the Apprise configuration page. If the creation fails,
    displays an error message and re-renders the template with the form data.

    Returns:
        A rendered template (GET), or a redirect to the Apprise configuration
        page (POST).
    """
    form = AppriseForm()

    if form.validate_on_submit():
        apprise = AppriseURL(
            label=form.label.data.strip(),
            url=form.url.data.strip(),
            enabled=form.enabled.data,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(apprise)
        db.session.commit()
        flash(_("Apprise destination created successfully."), "success")
        log_info_message(f"Apprise created by {current_user.username}: {apprise.label}")
        return redirect(url_for("apprise_routes.config"))

    return render_template("apprise/create_apprise.html", form=form)


# ---------------------------------------------------------------------
# Apprise list view route
# ---------------------------------------------------------------------
@bp.route("/config")
@login_required
def config():
    """
    Displays the Apprise configuration page, which lists all Apprise destinations
    for the current user.

    Retrieves a list of AppriseURL objects for the current user, sorted in
    descending order by creation date. Passes this list, along with other
    necessary data, to the apprise_config.html template for rendering.

    Returns:
        A rendered template (apprise_config.html) with the list of Apprise
        destinations.
    """

    apprise_urls = (
        AppriseURL.query.filter_by(user_id=current_user.id)
        .order_by(AppriseURL.created_at.desc())
        .all()
    )
    return render_template("apprise/list_apprise.html", destinations=apprise_urls)


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
    apprise = AppriseURL.query.get_or_404(id)
    form = AppriseForm(obj=apprise)

    if form.validate_on_submit():
        apprise.label = form.label.data.strip()
        apprise.url = form.url.data.strip()
        apprise.enabled = form.enabled.data
        db.session.commit()
        log_info_message(
            f"Apprise updated by {current_user.username}: ID={apprise.id}, label='{apprise.label}'"
        )
        flash(_("Apprise destination updated successfully."), "success")
        return redirect(url_for("apprise_routes.config"))

    return render_template("apprise/edit_apprise.html", form=form, apprise=apprise)


# ---------------------------------------------------------------------
# Apprise delete route
# ---------------------------------------------------------------------
@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_apprise(id):
    """
    Deletes an Apprise destination.

    Retrieves the AppriseURL object by its ID, deletes it from the database,
    and commits the changes. If the deletion is successful, displays a success
    message and redirects to the Apprise configuration page.

    Args:
        id (int): The ID of the AppriseURL object to delete.

    Returns:
        A redirect to the Apprise configuration page.
    """
    apprise = AppriseURL.query.get_or_404(id)
    db.session.delete(apprise)
    log_info_message(
        f"Apprise deleted by {current_user.username}: ID={apprise.id}, label='{apprise.label}'"
    )
    db.session.commit()
    flash(_("Apprise destination deleted."), "success")
    return redirect(url_for("apprise_routes.config"))
