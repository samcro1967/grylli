"""
# ---------------------------------------------------------------------
# login_form.py
# Path: login_form.py (relative to project root)
# Flask-WTF form for user login in Grylli.
# Used for standard username/password authentication.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

# ---------------------------------------------------------------------
# LoginForm Definition
# ---------------------------------------------------------------------


class LoginForm(FlaskForm):
    """
    WTForms form for user login.

    Fields:
        - username: The user's username (required).
        - password: The user's password (required).
        - submit: Submit button to log in.

    Notes:
        - All field labels are wrapped with Flask-Babel _l() for i18n.
        - CSRF protection is disabled via Meta subclass for use during automated testing.
    """

    username = StringField(
        _l("Username"), validators=[DataRequired()], description="Account username (required)."
    )
    password = PasswordField(
        _l("Password"), validators=[DataRequired()], description="Account password (required)."
    )
    submit = SubmitField(_l("Log In"))

    class Meta:
        """
        WTForms Meta subclass for form configuration.
        CSRF is disabled for this form, primarily for automated testing scenarios.
        """

        csrf = False  # ⛔ disable CSRF during tests
