"""
# ---------------------------------------------------------------------
# signup_form.py
# app/forms/signup_form.py
# Form definitions for user signup functionality in the Grylli project.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ---------------------- Imports (PEP8 ordering) -----------------------
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

# ---------------------------------------------------------------------
# SignupForm Class
# ---------------------------------------------------------------------


class SignupForm(FlaskForm):
    """
    Form for registering a new user.
    Collects username, email, password, and registration PIN.

    Fields:
        - username: Displayed as "Username", 3-64 chars, required.
        - email: Displayed as "Email", must be valid, max 120 chars, required.
        - password: Displayed as "Password", minimum 8 chars, required.
        - confirm_password: Must match password field, required.
        - registration_pin: Displayed as "Registration PIN", 6-64 chars, required.
        - submit: Submit button ("Register").
    """

    # ---------------------- Username Field ----------------------------
    username = StringField(
        _l("Username"),
        validators=[
            DataRequired(),  # Must be provided
            Length(min=3, max=64),  # Minimum and maximum length
        ],
    )

    # ---------------------- Email Field -------------------------------
    email = StringField(
        _l("Email"),
        validators=[
            DataRequired(),  # Must be provided
            Email(),  # Must be a valid email address
            Length(max=120),  # Maximum length
        ],
    )

    # ---------------------- Password Field ----------------------------
    password = PasswordField(
        _l("Password"),
        validators=[
            DataRequired(),  # Must be provided
            Length(min=8),  # Enforce minimum password length
        ],
    )

    # ------------------ Confirm Password Field ------------------------
    confirm_password = PasswordField(
        _l("Confirm Password"),
        validators=[
            DataRequired(),  # Must be provided
            EqualTo("password", message=_l("Passwords must match")),
        ],
    )

    # ------------------ Registration PIN Field ------------------------
    registration_pin = StringField(
        _l("Registration PIN"),
        validators=[
            DataRequired(),  # Must be provided
            Length(min=6, max=64),  # Minimum and maximum length, adjust as needed
        ],
    )

    # ---------------------- Submit Button -----------------------------
    submit = SubmitField(_l("Register"))

    # ---------------------- Cancel Button -----------------------------
    cancel = SubmitField(_l("Cancel"))
