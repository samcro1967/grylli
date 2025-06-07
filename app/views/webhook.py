"""
# ---------------------------------------------------------------------
# webhook.py
# app/views/webhook.py
# Webhook creation, configuration, and test endpoints for Grylli.
# ---------------------------------------------------------------------
"""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _  # ✅ Add translation support
from flask_login import current_user, login_required

from app.forms.webhook_form import WebhookForm
from app.models import Webhook, db
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("webhook", __name__)


# ---------------------------------------------------------------------
# View:  Create webhooks
# ---------------------------------------------------------------------
@bp.route("/webhooks/create/", methods=["GET", "POST"])
@login_required
def create_webhook():
    """
    Handle the creation of a new webhook.

    This view supports both GET and POST requests. On GET requests, it renders the
    form for creating a new webhook. On POST requests, it processes the submitted form
    data to create a new webhook entry in the database if the form is valid. After
    successful creation, it flashes a success message and redirects to the webhook
    configuration page.

    Returns:
        str: The rendered template for creating a webhook with the form instance.
    """

    form = WebhookForm()

    if form.validate_on_submit():
        webhook = Webhook(
            label=form.label.data.strip(),
            endpoint=form.endpoint.data.strip(),
            description=form.description.data.strip(),
            enabled=form.enabled.data,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(webhook)
        db.session.commit()
        flash(_("Webhook created successfully."), "success")
        log_info_message(f"Webhook created by {current_user.username}: {webhook.label}")
        return redirect(url_for("webhook.config"))

    return render_template("webhook/create_webhook.html", form=form)


# ---------------------------------------------------------------------
# View:  View webhooks
# ---------------------------------------------------------------------
@bp.route("/config")
@login_required
def config():
    """
    Handles the GET request to render the webhook configuration page.

    This view renders the webhook configuration page which displays the list of
    webhooks created by the current user. The webhooks are ordered by their creation
    time in descending order (newest first).

    Returns:
        str: The rendered template for the webhook configuration page.
    """

    webhooks = (
        Webhook.query.filter_by(user_id=current_user.id).order_by(Webhook.created_at.desc()).all()
    )
    return render_template("webhook/list_webhooks.html", webhooks=webhooks)


# ---------------------------------------------------------------------
# View:  Edit webhooks
# ---------------------------------------------------------------------
@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_webhook(id):
    """
    Handles the GET and POST requests to edit a webhook.

    This view renders the edit webhook page which displays the form populated with
    the webhook data. On a valid form submission, it updates the webhook entry in the
    database and flashes a success message. If the form is invalid, it renders the
    form again with the populated values.

    Args:
        id (int): The unique identifier of the webhook to edit.

    Returns:
        str: The rendered template for the edit webhook page.
    """
    webhook = Webhook.query.get_or_404(id)
    form = WebhookForm(obj=webhook)

    if form.validate_on_submit():
        webhook.label = form.label.data.strip()
        webhook.endpoint = form.endpoint.data.strip()
        webhook.description = form.description.data.strip()
        webhook.enabled = form.enabled.data
        db.session.commit()
        flash(_("Webhook updated successfully."), "success")
        return redirect(url_for("webhook.config"))

    return render_template("webhook/edit_webhook.html", form=form, webhook=webhook)


# ---------------------------------------------------------------------
# View:  Delete webhooks
# ---------------------------------------------------------------------
@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_webhook(id):
    """
    Handles the POST request to delete a webhook.

    This view is only accessible by a POST request and is protected by the login
    required decorator. It gets the webhook instance from the database by its
    unique identifier in the URL, deletes it, and flashes a success message.
    After deletion, it redirects to the webhook configuration page.

    Args:
        id (int): The unique identifier of the webhook to delete.

    Returns:
        str: The rendered template for the webhook configuration page.
    """
    webhook = Webhook.query.get_or_404(id)
    db.session.delete(webhook)
    db.session.commit()
    flash(_("Webhook deleted."), "success")
    return redirect(url_for("webhook.config"))


# ---------------------------------------------------------------------
# View:  Test webhooks
# ---------------------------------------------------------------------
@bp.route("/<int:id>/test", methods=["POST"])
@login_required
def test_webhook(id):
    """
    Handles the POST request to test a webhook.

    This view is only accessible by a POST request and is protected by the login
    required decorator. It gets the webhook instance from the database by its
    unique identifier in the URL, sends a test notification to the webhook, and
    flashes a success or failure message depending on the result of the test
    request. After the test, it redirects to the webhook configuration page.

    Args:
        id (int): The unique identifier of the webhook to test.

    Returns:
        str: The rendered template for the webhook configuration page.
    """
    from app.models import Webhook
    from app.services.webhook import send_test_webhook_notification

    webhook = Webhook.query.get_or_404(id)

    try:
        success, response = send_test_webhook_notification(webhook.endpoint)
        if success:
            flash(_("🧪 Webhook test sent successfully!"), "success")
        else:
            flash(_("🧪 Webhook test failed: ") + response, "danger")
    except Exception as e:
        log_exception_with_traceback("Webhook test failed", e)
        flash(_("🧪 Error sending webhook test."), "danger")

    return redirect(url_for("webhook.config"))
