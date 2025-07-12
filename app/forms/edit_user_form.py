"""
# ---------------------------------------------------------------------
# edit_user_form.py
# Path: edit_user_form.py (relative to project root)
# Flask-WTF form for editing an existing user in Grylli.
# Allows admins to update user details, role, and set/reset passwords.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp

# ---------------------------------------------------------------------
# EditUserForm Definition
# ---------------------------------------------------------------------


class EditUserForm(FlaskForm):
    """
    WTForms form for editing an existing user's details.

    Fields:
        - username: User's display or login name (required, 3–20 characters).
        - email: User's email address (required, must be valid).
        - role: Role assigned to the user ("admin" or "user", required).
        - new_password: Optionally set a new password (min 8 chars, must meet complexity requirements).
        - confirm_password: Confirmation for the new password (must match new_password).
        - submit: Submit button to update user.

    Password requirements (if setting a new password):
        - At least 8 characters.
        - At least one uppercase letter.
        - At least one lowercase letter.
        - At least one number.
        - At least one special character.
    """

    username = StringField(
        _l("Username"),
        validators=[DataRequired(), Length(min=3, max=20)],
        description="User's display or login name (required, 3–20 characters).",
    )
    email = StringField(
        _l("Email"),
        validators=[DataRequired(), Email()],
        description="User's email address (required, must be valid email).",
    )
    new_password = PasswordField(
        _l("New Password"),
        validators=[
            Optional(),
            Length(min=8),
            Regexp(r".*[A-Z].*", message=_l("Must have at least one uppercase letter")),
            Regexp(r".*[a-z].*", message=_l("Must have at least one lowercase letter")),
            Regexp(r".*\d.*", message=_l("Must have at least one number")),
            Regexp(r".*[\W_].*", message=_l("Must have at least one special character")),
        ],
        description="Optionally set a new password (min 8 chars, must meet complexity requirements).",
    )
    confirm_password = PasswordField(
        _l("Confirm New Password"),
        validators=[Optional(), EqualTo("new_password", message=_l("Passwords must match."))],
        description="Confirmation for the new password (must match new_password).",
    )
    submit = SubmitField(_l("Update User"))
