from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, EqualTo

class AccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    current_password = PasswordField("Current Password", validators=[Optional()])
    new_password = PasswordField("New Password", validators=[
        Optional(),
        EqualTo('confirm_password', message="Passwords must match"),
    ])
    confirm_password = PasswordField("Confirm New Password", validators=[Optional()])
    submit = SubmitField("Update Account")
