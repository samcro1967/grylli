# ---------------------------------------------------------------------
# secure_email_forms.py
# app/forms/secure_email_forms.py
# Forms for secure email messages and SMTP settings
# ---------------------------------------------------------------------

from flask_babel import _  # ✅ Babel translation
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
# Secure Email Message Form
# ---------------------------------------------------------------------
class EmailMessageForm(FlaskForm):
    label = StringField(_("Label"), validators=[DataRequired(), Length(max=100)])
    recipient = StringField(
        _("Recipient Email"), validators=[DataRequired(), Email(), Length(max=255)]
    )
    subject = StringField(_("Subject"), validators=[DataRequired(), Length(max=255)])
    body = TextAreaField(_("Message Body"), validators=[DataRequired()])
    submit = SubmitField(_("Save Message"))


# ---------------------------------------------------------------------
# User SMTP Settings Form
# ---------------------------------------------------------------------
class UserMailSettingsForm(FlaskForm):
    smtp_host = StringField(_("SMTP Host"), validators=[DataRequired(), Length(max=128)])
    smtp_port = IntegerField(
        _("SMTP Port"), validators=[DataRequired(), NumberRange(min=1, max=65535)]
    )
    smtp_username = StringField(_("SMTP Username"), validators=[DataRequired(), Length(max=128)])
    smtp_password = PasswordField(_("SMTP Password"), validators=[DataRequired(), Length(max=512)])
    use_tls = BooleanField(_("Use TLS"), default=True)
    enabled = BooleanField(_("Enable Email Sending"), default=True)
    submit = SubmitField(_("Save Settings"))


# ---------------------------------------------------------------------
# Attach Files Form (checklist style)
# ---------------------------------------------------------------------
class AttachFilesForm(FlaskForm):
    submit = SubmitField(_("Attach Selected Files"))
