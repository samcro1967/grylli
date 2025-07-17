"""
# ---------------------------------------------------------------------
# reset_password_form.py
# Path: app/forms/reset_password_form.py
# Flask-WTF form for resetting a user's password in Grylli.
# Used in the password reset (forgot password) flow.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length

# ======================
# Local Imports
# ======================
from app.forms.validators import validate_complex_password

# ---------------------------------------------------------------------
# ResetPasswordForm Definition
# ---------------------------------------------------------------------


class ResetPasswordForm(FlaskForm):
    """
    WTForms form for resetting a user's password.

    Fields:
        - username: The user's username (required).
        - email: Registered email address (required, must be valid).
        - password: New password to set (required, min 8 chars, must meet complexity).
        - confirm_password: Confirmation for new password (required, must match).
        - submit: Reset button.
        - cancel: Cancel button (returns to login page).
    Notes:
        - Uses custom validator `validate_complex_password` for strong password enforcement.
    """

    username = StringField(
        _l("Username"), validators=[DataRequired()], description="Account username (required)."
    )
    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="Registered email address (required, must be valid email).",
    )
    password = PasswordField(
        _l("New Password"),
        validators=[DataRequired(), Length(min=8), validate_complex_password],
        description="New password (required, minimum 8 characters, must meet complexity).",
    )
    confirm_password = PasswordField(
        _l("Confirm Password"),
        validators=[DataRequired(), EqualTo("password", message=_l("Passwords must match"))],
        description="Confirmation for new password (required, must match password).",
    )
    submit = SubmitField(_l("Reset Password"))
    cancel = SubmitField(_l("Cancel"))
