"""
# ---------------------------------------------------------------------
# admin_creation_form.py
# Path: admin_creation_form.py (relative to project root)
# WTForms form for first-time admin user creation during Grylli bootstrap.
# Used to initialize the application with its first admin account.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

# ---------------------------------------------------------------------
# AdminCreationForm Definition
# ---------------------------------------------------------------------


class AdminCreationForm(FlaskForm):
    """
    WTForms form for creating the initial admin user during the bootstrap flow.

    Fields:
        - username: Desired admin username (3–20 characters, required).
        - email: Admin email address (must be valid, required).
        - password: Admin password (min 8 characters, required).
        - confirm_password: Confirmation for the admin password (must match, required).
        - submit: Submit button.

    Notes:
        - All user-facing field labels are wrapped with Flask-Babel _l() for i18n.
        - Password confirmation enforces match via EqualTo validator.
    """

    username = StringField(
        _l("Username"),
        validators=[DataRequired(), Length(min=3, max=20)],
        description="Desired admin username (required, 3-20 characters).",
    )
    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="Admin email address (required, must be valid email).",
    )
    password = PasswordField(
        _l("Password"),
        validators=[DataRequired(), Length(min=8)],
        description="Admin password (required, minimum 8 characters).",
    )
    confirm_password = PasswordField(
        _l("Confirm Password"),
        validators=[DataRequired(), EqualTo("password", message=_l("Passwords must match."))],
        description="Confirmation of admin password (required, must match password).",
    )
    submit = SubmitField(_l("Create Admin"))
