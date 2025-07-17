# app/forms/mfa_form.py

from flask_babel import _
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


# ---------------------------------------------------------------------
# MFA Settings Form
# ---------------------------------------------------------------------
class MFASettingsForm(FlaskForm):
    """Single form for enabling/disabling MFA."""

    enabled = BooleanField(_("Enabled"))
    code = StringField(_("Authenticator Code"))
    submit = SubmitField(_("Save"))


# ---------------------------------------------------------------------
# MFA CHallenge Form
# ---------------------------------------------------------------------
class MFAChallengeForm(FlaskForm):
    """Form for entering a TOTP or recovery code during login."""

    code = StringField(
        _("Authentication Code"),
        validators=[
            DataRequired(message=_("Please enter your authentication code.")),
            Length(min=6, max=16, message=_("Enter a valid 6-digit code or recovery code.")),
            Regexp(r"^[0-9A-Za-z]+$", message=_("Invalid code format.")),
        ],
        render_kw={"autofocus": True, "autocomplete": "one-time-code"},
    )
    submit = SubmitField(_("Verify"))
