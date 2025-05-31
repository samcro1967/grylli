
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

# ---------------------------------------------------------------------
# Secure Email Message Form
# ---------------------------------------------------------------------
class EmailMessageForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=100)])
    recipient = StringField("Recipient Email", validators=[DataRequired(), Email(), Length(max=255)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=255)])
    body = TextAreaField("Message Body", validators=[DataRequired()])
    submit = SubmitField("Save Message")

# ---------------------------------------------------------------------
# User SMTP Settings Form
# ---------------------------------------------------------------------
class UserMailSettingsForm(FlaskForm):
    smtp_host = StringField("SMTP Host", validators=[DataRequired(), Length(max=128)])
    smtp_port = IntegerField("SMTP Port", validators=[DataRequired(), NumberRange(min=1, max=65535)])
    smtp_username = StringField("SMTP Username", validators=[DataRequired(), Length(max=128)])
    smtp_password = PasswordField("SMTP Password", validators=[DataRequired(), Length(max=512)])
    use_tls = BooleanField("Use TLS", default=True)
    enabled = BooleanField("Enable Email Sending", default=True)
    submit = SubmitField("Save Settings")

# ---------------------------------------------------------------------
# Attach Files Form (checklist style)
# ---------------------------------------------------------------------
class AttachFilesForm(FlaskForm):
    # This will be populated dynamically in the view
    submit = SubmitField("Attach Selected Files")
