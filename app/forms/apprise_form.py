"""
# ---------------------------------------------------------------------
# apprise_form.py
# Path: apprise_form.py (relative to project root)
# Flask-WTF form definitions for managing Apprise notification destinations.
# Used to add and configure Apprise services in Grylli.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import URL, DataRequired, Length, Regexp

# ---------------------------------------------------------------------
# AppriseConfigForm Definition
# ---------------------------------------------------------------------


class AppriseConfigForm(FlaskForm):
    """
    WTForms form for editing an existing Apprise notification configuration.

    Fields:
        - label: Friendly name for the Apprise destination (required, 2–50 chars).
        - url: Full Apprise notification URL (required, must be valid URL).
        - submit: Save button.
    """

    label = StringField(
        _l("Label"),
        validators=[DataRequired(), Length(min=2, max=50)],
        description="Friendly name for the Apprise destination (required, 2–50 characters).",
    )
    url = StringField(
        _l("Apprise URL"),
        validators=[DataRequired(), URL()],
        description="Full Apprise URL for messages (required, must be a valid URL).",
    )
    submit = SubmitField(_l("Save"))


# ---------------------------------------------------------------------
# AppriseForm Definition
# ---------------------------------------------------------------------


class AppriseForm(FlaskForm):
    """
    WTForms form for creating a new Apprise notification destination.

    Fields:
        - label: Friendly name for the Apprise destination (required, 2–100 chars).
        - url: Apprise URL (required, must match Apprise URL scheme, min 5 chars, max 1000).
        - enabled: Toggle to enable or disable this destination.
        - submit: Create button.
    """

    label = StringField(
        _l("Label"),
        validators=[DataRequired(), Length(min=2, max=100)],
        description="Friendly name for the Apprise destination (required, 2–100 characters).",
    )
    url = StringField(
        _l("Apprise URL"),
        validators=[
            DataRequired(),
            Regexp(r"^[a-zA-Z][a-zA-Z0-9+.-]*://.+$", message=_l("Invalid Apprise URL")),
            Length(min=5, max=1000),
        ],
        description="Apprise URL (required, must match URL scheme, 5–1000 characters).",
    )
    enabled = BooleanField(
        _l("Enabled"),
        default=True,
        description="Whether this Apprise destination is enabled (default: True).",
    )
    submit = SubmitField(_l("Create Destination"))
