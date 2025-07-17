"""
# ---------------------------------------------------------------------
# email_form.py
# Path: email_form.py (relative to project root)
# Flask-WTF form definitions for secure email messaging and SMTP settings in Grylli.
# Forms include: secure message creation, user SMTP config, file attachment, and SMTP config assignment.
# ---------------------------------------------------------------------
"""

from flask_babel import lazy_gettext as _l

# ======================
# Third-Party Imports
# ======================
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

# ---------------------------------------------------------------------
# EmailMessageForm Definition
# ---------------------------------------------------------------------


class EmailMessageForm(FlaskForm):
    """
    WTForms form for composing a secure email message.

    Fields:
        - label: Friendly label for the message (required, max 100 chars).
        - recipient: Recipient's email address (required, valid email, max 255 chars).
        - subject: Email subject line (required, max 255 chars).
        - body: Email body/message content (required, text).
        - submit: Save button.
    """

    label = StringField(
        _l("Label"),
        validators=[DataRequired(), Length(max=100)],
        description="Friendly label for the secure message (required, max 100 characters).",
    )
    recipient = StringField(
        _l("Recipient Email"),
        validators=[DataRequired(), Email(), Length(max=255)],
        description="Recipient's email address (required, must be valid email, max 255 characters).",
    )
    subject = StringField(
        _l("Subject"),
        validators=[DataRequired(), Length(max=255)],
        description="Subject line for the email (required, max 255 characters).",
    )
    body = TextAreaField(
        _l("Message Body"),
        validators=[DataRequired()],
        description="Body content of the email message (required).",
    )
    submit = SubmitField(_l("Save Message"))


# ---------------------------------------------------------------------
# UserMailSettingsForm Definition
# ---------------------------------------------------------------------


class UserMailSettingsForm(FlaskForm):
    """
    WTForms form for configuring per-user SMTP (email sending) settings.

    Fields:
        - smtp_host: SMTP server hostname or IP (required, max 128 chars).
        - smtp_port: SMTP server port (required, 1–65535).
        - smtp_username: Username for SMTP authentication (required, max 128 chars).
        - smtp_password: Password for SMTP authentication (required, max 512 chars).
        - use_tls: Whether to use TLS encryption (boolean, default: True).
        - enabled: Whether email sending is enabled for this user (boolean, default: True).
        - submit: Save button.
    """

    smtp_host = StringField(
        _l("SMTP Host"),
        validators=[DataRequired(), Length(max=128)],
        description="SMTP server hostname or IP address (required, max 128 characters).",
    )
    smtp_port = IntegerField(
        _l("SMTP Port"),
        validators=[DataRequired(), NumberRange(min=1, max=65535)],
        description="SMTP server port (required, 1–65535).",
    )
    smtp_username = StringField(
        _l("SMTP Username"),
        validators=[DataRequired(), Length(max=128)],
        description="Username for SMTP authentication (required, max 128 characters).",
    )
    smtp_password = PasswordField(
        _l("SMTP Password"),
        validators=[DataRequired(), Length(max=512)],
        description="Password for SMTP authentication (required, max 512 characters).",
    )
    use_tls = BooleanField(
        _l("Use TLS"), default=True, description="Enable TLS encryption for SMTP (default: True)."
    )
    enabled = BooleanField(
        _l("Enable Email Sending"),
        default=True,
        description="Enable or disable email sending for this user (default: True).",
    )
    submit = SubmitField(_l("Save Settings"))


# ---------------------------------------------------------------------
# AttachFilesForm Definition (for checklist-style file selection)
# ---------------------------------------------------------------------


class AttachFilesForm(FlaskForm):
    """
    WTForms form for attaching files to a secure message.

    Fields:
        - submit: Button to attach selected files.
    Note:
        The actual file fields (checkboxes or inputs) are populated dynamically in the view.
    """

    submit = SubmitField(_l("Attach Selected Files"))


# ---------------------------------------------------------------------
# AssignSmtpForm Definition (CSRF-only form for radio selection)
# ---------------------------------------------------------------------


class AssignSmtpForm(FlaskForm):
    """
    Empty WTForms form for assigning SMTP configs to messages.
    Used primarily to enforce CSRF protection in views handling SMTP assignment.
    """

    pass
