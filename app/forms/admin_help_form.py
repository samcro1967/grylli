"""
app/forms/admin_help_form.py
Form for accessing the admin help page using a FERRET_KEY.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class AdminHelpForm(FlaskForm):
    """
    Form that prompts for a Ferret Key to access the admin help page.
    """

    class Meta:
        csrf = False  # ✅ Prevent CSRF validation during testing

    ferret_key = PasswordField("Ferret Key", validators=[DataRequired()])
    submit = SubmitField("Submit")
