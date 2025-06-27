# ---------------------------------------------------------------------
# webhook.py
# app/views/webhook.py
# Webhook creation, configuration, and test endpoints for Grylli.
# ---------------------------------------------------------------------

from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.forms.webhook_form import WebhookForm
from app.models import Webhook, db
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("webhook", __name__)


@bp.route("/webhooks/create/", methods=["GET", "POST"])
@login_required
def create_webhook():
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
            log_info_message(f"Webhook created by {current_user.username}: {webhook.label}")
            return redirect(url_for("webhook.config"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Failed to create webhook", e)
            flash(_("Failed to create webhook."), "danger")

    return render_template("webhook/create_webhook.html", form=form)


@bp.route("/config")
@login_required
def config():
    try:
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
        return render_template(template, webhooks=webhooks)
    except Exception as e:
        log_exception_with_traceback("Failed to load webhook config", e)
        flash(_("Could not load webhooks."), "danger")
        return redirect(url_for("home.index"))



@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_webhook(id):

    webhook = db.session.get(Webhook, id)
    if webhook is None:
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
            log_info_message(f"Webhook ID={webhook.id} updated by {current_user.username}")
            return redirect(url_for("webhook.config"))
        except Exception as e:
            db.session.rollback()
            log_exception_with_traceback("Failed to update webhook", e)
            flash(_("Failed to update webhook."), "danger")

    return render_template("webhook/edit_webhook.html", form=form, webhook=webhook)


@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_webhook(id):

    webhook = db.session.get(Webhook, id)
    if webhook is None:
        abort(404)

    try:
        db.session.delete(webhook)
        db.session.commit()
        flash(_("Webhook deleted."), "success")
        log_info_message(f"Webhook ID={webhook.id} deleted by {current_user.username}")
    except Exception as e:
        db.session.rollback()
        log_exception_with_traceback("Failed to delete webhook", e)
        flash(_("Failed to delete webhook."), "danger")

    return redirect(url_for("webhook.config"))


@bp.route("/test/<int:id>", methods=["POST"])
@login_required
def test_webhook(id):
    from app.services.webhook import send_test_webhook_notification

    webhook = db.session.get(Webhook, id)
    if webhook is None:
        abort(404)

    try:
        ok, msg = send_test_webhook_notification(webhook.endpoint)
        if ok:
            flash(_("Test notification sent."), "success")
        else:
            flash(_("Test failed: %(msg)s", msg=msg), "danger")
        log_info_message(f"Webhook test initiated by {current_user.username}: {webhook.label}")
    except Exception as e:
        log_exception_with_traceback("Webhook test failed", e)
        flash(_("Unexpected error sending test."), "danger")

    return redirect(url_for("webhook.config"))
