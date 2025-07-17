"""
# ---------------------------------------------------------------------
# user_smtp_form.py
# app/forms/user_smtp_form.py
# Defines the form for configuring user-specific SMTP email settings.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ------------------------ Imports (PEP8 order) -----------------------
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

# ---------------------------------------------------------------------
# SmtpForm Class
# ---------------------------------------------------------------------


class SmtpForm(FlaskForm):
    """
    Form for users to configure their SMTP server settings for emails.

    Fields:
        - label: User-defined label for identifying this SMTP config.
        - smtp_host: SMTP server address.
        - smtp_port: SMTP server port (1-65535).
        - smtp_username: SMTP login username (must be a valid email).
        - smtp_password: SMTP password (optional, max 512 characters).
        - use_tls: Checkbox for enabling TLS (default: True).
        - enabled: Checkbox for activating this config (default: True).
        - submit: Submit button ("Save").
    """

    # ---------------------- SMTP Label Field --------------------------
    label = StringField(_l("Label"), validators=[DataRequired()])  # User must provide a label

    # ---------------------- SMTP Host Field ---------------------------
    smtp_host = StringField(
        _l("SMTP Host"), validators=[DataRequired()]  # SMTP host must be provided
    )

    # ---------------------- SMTP Port Field ---------------------------
    smtp_port = IntegerField(
        _l("SMTP Port"),
        validators=[
            DataRequired(),  # Must provide port number
            NumberRange(min=1, max=65535),  # Valid port range
        ],
    )

    # ---------------------- SMTP Username Field -----------------------
    smtp_username = StringField(
        _l("SMTP Username"),
        validators=[
            DataRequired(),  # Must provide username
            Email(),  # Must be valid email address
        ],
    )

    # ---------------------- SMTP Password Field -----------------------
    smtp_password = PasswordField(
        _l("SMTP Password"),
        validators=[
            Optional(),  # Password is optional
            Length(max=512),  # Limit length for security
        ],
    )

    # ---------------------- Use TLS Field -----------------------------
    use_tls = BooleanField(_l("Use TLS"), default=True)  # Use TLS by default for security

    # ---------------------- Enabled Field -----------------------------
    enabled = BooleanField(_l("Enabled"), default=True)  # Enable this SMTP config by default

    # ---------------------- Submit Button -----------------------------
    submit = SubmitField(_l("Save"))
