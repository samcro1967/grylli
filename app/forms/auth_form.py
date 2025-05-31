"""
# ---------------------------------------------------------------------
# auth_form.py
# Path: app/forms/auth_form.py
# Flask-WTF forms for authentication: forgot username and forgot password.
# Used in Grylli authentication and account recovery flows.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.forms.validators import validate_complex_password

# ---------------------------------------------------------------------
# ForgotUsernameForm Definition
# ---------------------------------------------------------------------


class ForgotUsernameForm(FlaskForm):
    """
    WTForms form for requesting a username reminder via email.

    Fields:
        - email: The user's registered email address (required, must be valid).
        - submit: Submit button to trigger username reminder.
        - cancel: Cancel button (returns to login page).
    """

    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="Registered email address (required, must be a valid email).",
    )
    submit = SubmitField(_l("Send Username"))
    cancel = SubmitField(_l("Cancel"))


# ---------------------------------------------------------------------
# ForgotPasswordForm Definition
# ---------------------------------------------------------------------


class ForgotPasswordForm(FlaskForm):
    """
    WTForms form for requesting a password reset link via email.

    Fields:
        - username: The user's username (required).
        - email: The user's registered email address (required, must be valid).
        - submit: Submit button to trigger reset link email.
        - cancel: Cancel button (returns to login page).
    """

    username = StringField(
        _l("Username"), validators=[DataRequired()], description="Account username (required)."
    )
    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="Registered email address (required, must be a valid email).",
    )
    submit = SubmitField(_l("Send Reset Link"))
    cancel = SubmitField(_l("Cancel"))


# ---------------------------------------------------------------------
