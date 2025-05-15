from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, Length, Regexp

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')], validators=[DataRequired()])

    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=8),
        Regexp(r'.*[A-Z].*', message="Must have at least one uppercase letter"),
        Regexp(r'.*[a-z].*', message="Must have at least one lowercase letter"),
        Regexp(r'.*\d.*', message="Must have at least one number"),
        Regexp(r'.*[\W_].*', message="Must have at least one special character"),
    ])

    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('new_password', message='Passwords must match.')
    ])

    submit = SubmitField('Update User')
