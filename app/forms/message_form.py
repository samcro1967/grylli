"""
# ---------------------------------------------------------------------
# message_form.py
# Path: message_form.py (relative to project root)
# Flask-WTF forms for message content and scheduling in Grylli.
# Defines MessageForm for composing messages and ScheduleForm for scheduling.
# ---------------------------------------------------------------------
"""

from flask import current_app
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm

# ======================
# Third-Party Imports
# ======================
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

# ---------------------------------------------------------------------
# Duration Units (for SelectFields or display)
# ---------------------------------------------------------------------
DURATION_UNITS = [
    ("minutes", _l("Minutes")),
    ("hours", _l("Hours")),
    ("days", _l("Days")),
    ("weeks", _l("Weeks")),
    ("months", _l("Months")),
    ("years", _l("Years")),
]

# ---------------------------------------------------------------------
# MessageForm Definition
# ---------------------------------------------------------------------


class MessageForm(FlaskForm):
    """
    WTForms form for composing or editing a message.

    Fields:
        - label: User-defined label for the message (required, max 100 chars).
        - subject: Subject/title for the message (required, max 200 chars).
        - content: Main message body/content (required).
    """

    label = StringField(
        label=_l("Label"),
        validators=[
            DataRequired(message=_l("Label is required.")),
            Length(max=100, message=_l("Label must be 100 characters or fewer.")),
        ],
        description="User-defined label for the message (required, max 100 characters).",
    )

    subject = StringField(
        label=_l("Subject"),
        validators=[
            DataRequired(message=_l("Subject is required.")),
            Length(max=200, message=_l("Subject must be 200 characters or fewer.")),
        ],
        description="Subject or title for the message (required, max 200 characters).",
    )

    content = TextAreaField(
        label=_l("Content"),
        validators=[DataRequired(message=_l("Content is required."))],
        description="Main body/content of the message (required).",
    )


# ---------------------------------------------------------------------
# ScheduleForm Definition
# ---------------------------------------------------------------------


class ScheduleForm(FlaskForm):
    """
    WTForms form for specifying check-in and grace period durations for a message.

    Fields:
        - checkin_years/months/weeks/days/hours/minutes: Check-in interval fields (all optional, default=0).
        - grace_years/months/weeks/days/hours/minutes: Grace period fields (all optional, default=0).
        - submit: Submit button to save schedule.
    Notes:
        - All fields default to zero (no interval) unless specified.
        - NumberRange(min=0) ensures no negative durations.
    """

    # Check-in Duration Fields
    checkin_years = IntegerField(_l("Years"), validators=[NumberRange(min=0)], default=0)
    checkin_months = IntegerField(_l("Months"), validators=[NumberRange(min=0)], default=0)
    checkin_weeks = IntegerField(_l("Weeks"), validators=[NumberRange(min=0)], default=0)
    checkin_days = IntegerField(_l("Days"), validators=[NumberRange(min=0)], default=0)
    checkin_hours = IntegerField(_l("Hours"), validators=[NumberRange(min=0)], default=0)
    checkin_minutes = IntegerField(_l("Minutes"), validators=[NumberRange(min=0)], default=0)

    # Grace Period Duration Fields
    grace_years = IntegerField(_l("Years"), validators=[NumberRange(min=0)], default=0)
    grace_months = IntegerField(_l("Months"), validators=[NumberRange(min=0)], default=0)
    grace_weeks = IntegerField(_l("Weeks"), validators=[NumberRange(min=0)], default=0)
    grace_days = IntegerField(_l("Days"), validators=[NumberRange(min=0)], default=0)
    grace_hours = IntegerField(_l("Hours"), validators=[NumberRange(min=0)], default=0)
    grace_minutes = IntegerField(_l("Minutes"), validators=[NumberRange(min=0)], default=0)

    submit = SubmitField(_l("Save Schedule"))
