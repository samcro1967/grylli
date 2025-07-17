"""
# ---------------------------------------------------------------------
# create_user_form.py
# Path: app/forms/create_user_form.py
# Flask-WTF form for creating a new user in Grylli.
# Used by admins to add users with username, email, password, and role.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

# ---------------------------------------------------------------------
# CreateUserForm Definition
# ---------------------------------------------------------------------


class CreateUserForm(FlaskForm):
    """
    WTForms form for creating a new user.

    Fields:
        - username: User's display or login name (required, 3–20 characters).
        - email: User's email address (required, must be valid).
        - new_password: Password for the new user (required, min 8 chars, must meet complexity requirements).
        - confirm_password: Confirmation for the new password (must match new_password).
        - role: Role assigned to the user ("admin" or "user", required).
        - submit: Submit button to create user.

    Password requirements:
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
        _l("Password"),
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(r".*[A-Z].*", message=_l("Must have at least one uppercase letter")),
            Regexp(r".*[a-z].*", message=_l("Must have at least one lowercase letter")),
            Regexp(r".*\d.*", message=_l("Must have at least one number")),
            Regexp(r".*[\W_].*", message=_l("Must have at least one special character")),
        ],
        description="Password for new user (min 8 chars, must meet complexity requirements).",
    )
    confirm_password = PasswordField(
        _l("Confirm Password"),
        validators=[DataRequired(), EqualTo("new_password", message=_l("Passwords must match."))],
        description="Confirmation for the new password.",
    )
    role = SelectField(
        _l("Role"),
        choices=[("user", _l("User")), ("admin", _l("Admin"))],
        validators=[DataRequired()],
        description="Role assigned to the user.",
    )
    submit = SubmitField(_l("Create User"))
