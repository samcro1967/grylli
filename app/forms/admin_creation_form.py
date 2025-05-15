# ---------------------------------------------------------------------
# admin_creation_form.py
# Form for first-time admin creation during bootstrap
# ---------------------------------------------------------------------

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email

class AdminCreationForm(FlaskForm):
    """
    WTForm for creating the initial admin user during the bootstrap flow.

    Fields:
        username (str): Desired admin username
        password (str): Admin password
        confirm_password (str): Must match password
        submit (SubmitField): Submit button
    """
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField("Create Admin")
