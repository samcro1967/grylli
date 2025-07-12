"""
# ---------------------------------------------------------------------
# webhook_form.py
# app/forms/webhook_form.py
# Forms for configuring and creating webhooks in Grylli.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ------------------------ Imports (PEP8 order) -----------------------
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

# ---------------------------------------------------------------------
# WebhookConfigForm
# ---------------------------------------------------------------------


class WebhookConfigForm(FlaskForm):
    """
    Simple form for configuring a webhook destination.

    Fields:
        - label: Short name for this webhook.
        - endpoint: The webhook URL (must be valid).
        - submit: Submit button ("Save").
    """

    # ---------------------- Label Field -------------------------------
    label = StringField(_l("Label"), validators=[DataRequired(), Length(min=2, max=50)])

    # ---------------------- Endpoint Field ----------------------------
    endpoint = StringField(_l("Webhook URL"), validators=[DataRequired(), URL()])

    # ---------------------- Submit Button -----------------------------
    submit = SubmitField(_l("Save"))


# ---------------------------------------------------------------------
# WebhookForm
# ---------------------------------------------------------------------


class WebhookForm(FlaskForm):
    """
    Form for creating or editing a webhook with additional options.

    Fields:
        - label: Display label for the webhook.
        - endpoint: The webhook endpoint URL.
        - description: Optional longer description.
        - enabled: Checkbox for activating webhook.
        - submit: Submit button ("Create Webhook").
    """

    # ---------------------- Label Field -------------------------------
    label = StringField(_l("Label"), validators=[DataRequired(), Length(min=2, max=100)])

    # ---------------------- Endpoint Field ----------------------------
    endpoint = StringField(
        _l("Endpoint"), validators=[DataRequired(), URL(), Length(min=5, max=1000)]
    )

    # ---------------------- Description Field -------------------------
    description = TextAreaField(_l("Description"), validators=[Optional(), Length(max=1000)])

    # ---------------------- Enabled Field -----------------------------
    enabled = BooleanField(_l("Enabled"), default=True)

    # ---------------------- Submit Button -----------------------------
    submit = SubmitField(_l("Create Webhook"))
