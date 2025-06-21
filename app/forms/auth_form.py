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
# ForgotPasswordForm Definition (Updated with Security Answers)
# ---------------------------------------------------------------------
class ForgotPasswordForm(FlaskForm):
    """
    WTForms form for requesting a password reset link via email and verifying
    user identity using security questions.

    Fields:
        - username: The user's username (required).
        - email: The user's registered email address (required, must be valid).
        - security_answer_0: Answer to first security question (optional, validated server-side).
        - security_answer_1: Answer to second security question (optional).
        - security_answer_2: Answer to third security question (optional).
        - submit: Submit button to continue flow.
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

    # Optional answer fields, validated only if shown
    security_answer_0 = StringField(
        _l("Answer 1"), description="Answer to the first security question."
    )
    security_answer_1 = StringField(
        _l("Answer 2"), description="Answer to the second security question."
    )
    security_answer_2 = StringField(
        _l("Answer 3"), description="Answer to the third security question."
    )

    submit = SubmitField(_l("Submit"))
    cancel = SubmitField(_l("Cancel"))
