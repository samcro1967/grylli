# ---------------------------------------------------------------------
# apprise.py
# app/views/apprise.py
# Blueprint for Apprise destination configuration and test routes.
# ---------------------------------------------------------------------

from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import _
from flask_login import current_user, login_required

from app.forms.apprise_form import AppriseForm
from app.models import AppriseURL, db
from app.services.apprise_utils import send_test_apprise_notification
from app.utils.logging import (
    log_debug_message,
    log_exception_with_traceback,
    log_info_message,
    log_user_action,
)

bp = Blueprint("apprise_routes", __name__)


# ---------------------------------------------------------------------
# Apprise test route
# ---------------------------------------------------------------------
@bp.route("<int:id>/test", methods=["POST"], strict_slashes=False)
@login_required
def test_apprise(id):
    """
    Sends a test notification for the specified Apprise destination.
    """

    log_info_message(f"Access - {current_user.username} - Apprise Test")

    apprise = db.session.execute(db.select(AppriseURL).filter_by(id=id)).scalar_one_or_none()

    if apprise is None:
        log_debug_message(f"Apprise test failed — destination ID={id} not found.")
        abort(404)

    try:
        success, response = send_test_apprise_notification(apprise.url)
        if success:
            flash(_("🧪 Test notification sent successfully!"), "success")
            log_user_action("Apprise", "Send Test", apprise)
        else:
            flash(_("🧪 Failed to send test notification: ") + response, "danger")
            log_user_action("Apprise", "Send Test", apprise, extra=f"FAILURE: {response}")
    except Exception as e:
        log_exception_with_traceback("Apprise test failed", e)
        flash(_("🧪 Error sending test notification."), "danger")

    return redirect(url_for("apprise_routes.config"))


# ---------------------------------------------------------------------
# Apprise create route
# ---------------------------------------------------------------------
@bp.route("create/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def create_apprise():
    """
    Handle creation of a new Apprise destination.
    """

    log_info_message(f"Access - {current_user.username} - Apprise Create")

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
            log_user_action("Apprise", "Create", apprise)

            if request.headers.get("HX-Request"):
                log_debug_message(f"HTMX create triggered for Apprise by {current_user.username}")
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "appriseListChanged"
                return response

            return redirect(url_for("apprise_routes.config"))

        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Failed to create Apprise destination", e)
            flash(_("Failed to create Apprise destination."), "danger")
    elif request.method == "POST":
        log_debug_message(f"Create form failed validation for Apprise by {current_user.username}")

    template = (
        "apprise/create_apprise_partial.html"
        if request.headers.get("HX-Request")
        else "apprise/create_apprise_full.html"
    )
    log_debug_message(f"Rendering create Apprise template: {template}")
    return render_template(template, form=form, is_edit=False)


# ---------------------------------------------------------------------
# Apprise list view route
# ---------------------------------------------------------------------
@bp.route("overview/", strict_slashes=False)
@login_required
def config():
    """
    Displays the Apprise configuration page with full or partial rendering.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Apprise Config")
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
        log_debug_message(f"Rendering Apprise overview template: {template}")
        return render_template(template, destinations=apprise_urls)

    except Exception as e:
        log_exception_with_traceback("Failed to load Apprise configuration", e)
        flash(_("Failed to load Apprise destinations."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# Apprise edit route
# ---------------------------------------------------------------------
@bp.route("edit/<int:id>", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_apprise(id):
    """
    Edits an existing Apprise destination.
    """

    log_info_message(f"Access - {current_user.username} - Apprise Edit")

    apprise = db.session.execute(
        db.select(AppriseURL).filter_by(id=id, user_id=current_user.id)
    ).scalar_one_or_none()

    if not apprise:
        log_debug_message(f"Edit access denied: Apprise ID={id} not found or unauthorized")
        abort(404)

    form = AppriseForm(obj=apprise)

    if form.validate_on_submit():
        try:
            apprise.label = form.label.data.strip()
            apprise.url = form.url.data.strip()
            apprise.enabled = form.enabled.data
            db.session.commit()
            flash(_("Apprise destination updated successfully."), "success")
            log_user_action("Apprise", "Edit", apprise)

            if request.headers.get("HX-Request"):
                log_debug_message(f"HTMX edit triggered for Apprise ID={id}")
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "appriseListChanged"
                return response

            return redirect(url_for("apprise_routes.config"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback(f"Failed to update Apprise ID={apprise.id}", e)
            flash(_("Failed to update Apprise destination."), "danger")
    elif request.method == "POST":
        log_debug_message(
            f"Edit form failed validation for Apprise ID={id} by {current_user.username}"
        )

    template = (
        "apprise/create_apprise_partial.html"
        if request.headers.get("HX-Request")
        else "apprise/edit_apprise.html"
    )
    log_debug_message(f"Rendering edit Apprise template: {template} for ID={id}")
    return render_template(template, form=form, apprise=apprise, is_edit=True)


# ---------------------------------------------------------------------
# Apprise delete route
# ---------------------------------------------------------------------
@bp.route("delete/<int:id>", methods=["POST"], strict_slashes=False)
@login_required
def delete_apprise(id):
    """
    Deletes an Apprise destination.
    """

    log_info_message(f"Access - {current_user.username} - Apprise Delete")

    apprise = db.session.execute(
        db.select(AppriseURL).filter_by(id=id, user_id=current_user.id)
    ).scalar_one_or_none()

    if not apprise:
        log_debug_message(f"Delete failed: Apprise ID={id} not found or unauthorized")
        abort(404)

    try:
        db.session.delete(apprise)
        db.session.commit()
        log_user_action("Apprise", "Delete", apprise)
        flash(_("Apprise destination deleted."), "success")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback(f"Failed to delete Apprise ID={apprise.id}", e)
        flash(_("Failed to delete Apprise destination."), "danger")

    return redirect(url_for("apprise_routes.config"))
