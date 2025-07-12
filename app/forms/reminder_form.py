# ---------------------------------------------------------------------
# reminder_form.py
# Path: app/forms/reminder_form.py
# Flask-WTF forms for creating/editing and scheduling reminders.
# ---------------------------------------------------------------------

from datetime import datetime

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

# ---------------------------------------------------------------------
# ReminderForm (No Scheduling Fields)
# ---------------------------------------------------------------------


class ReminderForm(FlaskForm):
    """
    WTForms form for composing or editing a reminder.

    Fields:
        - label: User-defined label for the reminder (required, max 100 chars).
        - subject: Subject/title for the reminder (required, max 200 chars).
        - content: Main reminder body/content (optional).
    """

    label = StringField(
        label=_l("Label"),
        validators=[
            DataRequired(message=_l("Label is required.")),
            Length(max=100, message=_l("Label must be 100 characters or fewer.")),
        ],
        description=_l("User-defined label for the reminder."),
    )

    subject = StringField(
        label=_l("Subject"),
        validators=[
            DataRequired(message=_l("Subject is required.")),
            Length(max=200, message=_l("Subject must be 200 characters or fewer.")),
        ],
        description=_l("Subject or title for the reminder."),
    )

    content = TextAreaField(
        label=_l("Content"),
        validators=[Optional()],
        description=_l("Main body/content of the reminder (optional)."),
    )

    submit = SubmitField(_l("Save Reminder"))


# ---------------------------------------------------------------------
# ScheduleReminderForm (Scheduling Fields Only)
# ---------------------------------------------------------------------


class ScheduleReminderForm(FlaskForm):
    """
    WTForms form for scheduling reminders.

    Fields:
        - start_at: When to start (required, future datetime).
        - recurrence_rule: iCal RRULE string (optional; one-time if blank).
        - end_at: When to stop recurrence (optional).
        - max_occurrences: Maximum times to send (optional).
    """

    start_at = DateTimeLocalField(
        label=_l("Start Date & Time"),
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message=_l("Start time is required."))],
        description=_l("When should the first reminder be sent?"),
        render_kw={"type": "datetime-local"},
    )

    recurrence_rule = StringField(
        label=_l("Recurrence Rule"),
        validators=[Optional(), Length(max=256)],
        description=_l(
            "(Optional) Enter recurrence as an RRULE (e.g., FREQ=MONTHLY;BYDAY=1MO). Leave blank for one-time."
        ),
    )

    end_at = DateTimeLocalField(
        label=_l("End Date"),
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
        description=_l("(Optional) Don't send reminders after this date."),
        render_kw={"type": "datetime-local"},
    )

    max_occurrences = IntegerField(
        label=_l("Max Occurrences"),
        validators=[Optional(), NumberRange(min=1)],
        description=_l("(Optional) Stop after this many reminders have been sent."),
    )

    submit = SubmitField(_l("Schedule Reminder"))

    def validate_start_at(self, field):
        now = datetime.now()

        # Remove timezone if present
        field_data_naive = field.data.replace(tzinfo=None) if field.data.tzinfo else field.data

        if field_data_naive <= now:
            raise ValidationError(_l("Start date/time must be in the future."))


# ---------------------------------------------------------------------
# Email Reminder Link Form
# ---------------------------------------------------------------------


class EmailReminderLinkForm(FlaskForm):
    smtp_config = SelectField(
        label=_l("SMTP Configuration"),
        validators=[Optional()],
        choices=[],  # dynamically populated
    )
    message = SelectField(
        label=_l("Message to Send"),
        validators=[Optional()],
        choices=[],  # dynamically populated
    )
    submit = SubmitField(_l("Save Email Reminder"))
