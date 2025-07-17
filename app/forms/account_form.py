"""
# ---------------------------------------------------------------------
# account_form.py
# Path: account_form.py (relative to project root)
# Flask-WTF form definition for managing/updating user account information.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Optional

# ---------------------------------------------------------------------
# AccountForm Definition
# ---------------------------------------------------------------------


class AccountForm(FlaskForm):
    """
    WTForms form for updating user account settings.

    Fields:
        - username: User's display or login name (required).
        - email: User's email address (required, must be valid email format).
        - current_password: Current password for verification (optional).
        - new_password: New password to set (optional, must match confirmation).
        - confirm_password: Confirmation of the new password (optional).
        - submit: Submit button to update the account.

    Notes:
        - All user-facing field labels are wrapped with Flask-Babel _l() for translation.
        - Validation ensures passwords match if provided.
    """

    username = StringField(
        _l("Username"),
        validators=[DataRequired()],
        description="User's display or login name (required).",
    )
    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="User's email address (required, must be a valid email format).",
    )
    current_password = PasswordField(
        _l("Current Password"),
        validators=[Optional()],
        description="Current password for verification (optional).",
    )
    new_password = PasswordField(
        _l("New Password"),
        validators=[Optional(), EqualTo("confirm_password", message=_l("Passwords must match"))],
        description="New password to set (optional, must match confirmation).",
    )
    confirm_password = PasswordField(
        _l("Confirm New Password"),
        validators=[Optional()],
        description="Confirmation of the new password (optional).",
    )
    submit = SubmitField(_l("Update Account"))
