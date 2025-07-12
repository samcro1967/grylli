# ---------------------------------------------------------------------
# webhook.py
# app/views/webhook.py
# Webhook creation, configuration, and test endpoints for Grylli.
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

from app.forms.webhook_form import WebhookForm
from app.models import Webhook, db
from app.utils.logging import (
    log_debug_message,
    log_exception_with_traceback,
    log_info_message,
    log_user_action,
)

bp = Blueprint("webhook", __name__)


@bp.route("webhooks/create/", methods=["GET", "POST"], strict_slashes=False)
@login_required
def create_webhook():

    log_info_message(f"Access - {current_user.username} - Webhook Create")

    form = WebhookForm()

    if form.validate_on_submit():
        try:
            webhook = Webhook(
                label=form.label.data.strip(),
                endpoint=form.endpoint.data.strip(),
                description=form.description.data.strip(),
                enabled=form.enabled.data,
                user_id=current_user.id,
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(webhook)
            db.session.commit()
            flash(_("Webhook created successfully."), "success")
            log_user_action("Webhook", "Create", webhook)

            if request.headers.get("HX-Request"):
                log_debug_message(f"HTMX webhook create triggered by {current_user.username}")
                response = make_response("", 204)
                response.headers["HX-Trigger"] = "webhookListChanged"
                return response

            return redirect(url_for("webhook.config"))

        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Failed to create webhook", e)
            flash(_("Failed to create webhook."), "danger")
    elif request.method == "POST":
        log_debug_message(f"Webhook create form failed validation for {current_user.username}")

    template = (
        "webhook/webhook_form_partial.html"
        if request.headers.get("HX-Request")
        else "webhook/create_webhook.html"
    )
    log_debug_message(f"Rendering webhook create template: {template}")
    return render_template(template, form=form, is_edit=False)


@bp.route("overview/", strict_slashes=False)
@login_required
def config():
    try:
        log_info_message(f"Access - {current_user.username} - Webhook Config")
        webhooks = (
            Webhook.query.filter_by(user_id=current_user.id)
            .order_by(Webhook.created_at.desc())
            .all()
        )
        template = (
            "webhook/list_webhooks_partial.html"
            if request.headers.get("HX-Request")
            else "webhook/list_webhooks_full.html"
        )
        log_debug_message(f"Rendering webhook config template: {template}")
        return render_template(template, webhooks=webhooks)

    except Exception as e:
        log_exception_with_traceback("Failed to load webhook config", e)
        flash(_("Could not load webhooks."), "danger")
        return redirect(url_for("home.index"))


@bp.route("edit/<int:id>", methods=["GET", "POST"], strict_slashes=False)
@login_required
def edit_webhook(id):
    try:
        log_info_message(f"Access - {current_user.username} - Webhook Edit")
        webhook = db.session.get(Webhook, id)
        if webhook is None:
            log_debug_message(f"Webhook edit failed: ID={id} not found")
            abort(404)

        form = WebhookForm(obj=webhook)

        if form.validate_on_submit():
            try:
                webhook.label = form.label.data.strip()
                webhook.endpoint = form.endpoint.data.strip()
                webhook.description = form.description.data.strip()
                webhook.enabled = form.enabled.data
                db.session.commit()
                flash(_("Webhook updated successfully."), "success")
                log_user_action("Webhook", "Edit", webhook)

                if request.headers.get("HX-Request"):
                    log_debug_message(f"HTMX webhook edit triggered for ID={id}")
                    response = make_response("", 204)
                    response.headers["HX-Trigger"] = "webhookListChanged"
                    return response

                return redirect(url_for("webhook.config"))

            except Exception as e:
                db.session.rollback()
                log_exception_with_traceback("Failed to update webhook", e)
                flash(_("Failed to update webhook."), "danger")

        elif request.method == "POST":
            log_debug_message(f"Webhook edit form failed validation for ID={id}")

        template = (
            "webhook/webhook_form_partial.html"
            if request.headers.get("HX-Request")
            else "webhook/edit_webhook.html"
        )
        log_debug_message(f"Rendering webhook edit template: {template}")
        return render_template(template, form=form, webhook=webhook, is_edit=True)

    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Error editing webhook", e)
        flash(_("Failed to load or update webhook config."), "danger")
        return redirect(url_for("webhook.config"))


@bp.route("delete/<int:id>", methods=["POST"], strict_slashes=False)
@login_required
def delete_webhook(id):
    log_info_message(f"Access - {current_user.username} - Webhook Delete")
    webhook = db.session.get(Webhook, id)
    if webhook is None:
        log_debug_message(f"Webhook delete failed: ID={id} not found")
        abort(404)

    try:
        db.session.delete(webhook)
        db.session.commit()
        flash(_("Webhook deleted."), "success")
        log_user_action("Webhook", "Delete", webhook)
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Failed to delete webhook", e)
        flash(_("Failed to delete webhook."), "danger")

    return redirect(url_for("webhook.config"))


@bp.route("test/<int:id>", methods=["POST"], strict_slashes=False)
@login_required
def test_webhook(id):

    log_info_message(f"Access - {current_user.username} - Webhook Test")

    from app.services.webhook import send_test_webhook_notification

    webhook = db.session.get(Webhook, id)
    if webhook is None:
        log_debug_message(f"Webhook test failed: ID={id} not found")
        abort(404)

    try:
        ok, msg = send_test_webhook_notification(webhook.endpoint)
        if ok:
            flash(_("Test notification sent."), "success")
            log_user_action("Webhook", "Send Test", webhook)
        else:
            flash(_("Test failed: %(msg)s", msg=msg), "danger")
            log_user_action("Webhook", "Send Test", webhook, extra=f"FAILURE: {msg}")
    except Exception as e:
        log_exception_with_traceback("Webhook test failed", e)
        flash(_("Unexpected error sending test."), "danger")

    return redirect(url_for("webhook.config"))
