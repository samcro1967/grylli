"""
# ---------------------------------------------------------------------
# security_questions_form.py
# app/forms/security_questions_form.py
# Form definitions for user security questions
# ---------------------------------------------------------------------
"""

from flask_babel import _  # ✅ For translation
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

# ---------------------------------------------------------------------
# Security question dropdown choices (translated)
# ---------------------------------------------------------------------
SECURITY_QUESTION_CHOICES = [
    ("", _("--- Select a question ---")),
    ("birth_city", _("In what city were you born?")),
    ("best_friend", _("What is the name of your childhood best friend?")),
    ("school_mascot", _("What was the mascot of the high school you graduated from?")),
    ("school_elementary", _("What is the name of the first elementary school you attended?")),
    ("mother_maiden", _("What is your mother’s maiden name?")),
    ("maternal_grandma_maiden", _("What is your maternal grandmother's maiden name?")),
    ("paternal_grandma_maiden", _("What is your paternal grandmother's maiden name?")),
    ("father_middle", _("What is your father's middle name?")),
    ("mother_middle", _("What is your mother's middle name?")),
]


# ---------------------------------------------------------------------
# Form: Set Security Questions
# ---------------------------------------------------------------------
class SecurityQuestionsForm(FlaskForm):
    question_1 = SelectField(
        _("Question 1"), choices=SECURITY_QUESTION_CHOICES, validators=[DataRequired()]
    )
    answer_1 = StringField(_("Answer 1"), validators=[DataRequired(), Length(min=2, max=255)])

    question_2 = SelectField(
        _("Question 2"), choices=SECURITY_QUESTION_CHOICES, validators=[DataRequired()]
    )
    answer_2 = StringField(_("Answer 2"), validators=[DataRequired(), Length(min=2, max=255)])

    question_3 = SelectField(
        _("Question 3"), choices=SECURITY_QUESTION_CHOICES, validators=[DataRequired()]
    )
    answer_3 = StringField(_("Answer 3"), validators=[DataRequired(), Length(min=2, max=255)])

    submit = SubmitField(_("Save Security Questions"))

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        questions = [self.question_1.data, self.question_2.data, self.question_3.data]
        if len(set(questions)) != 3:
            self.question_3.errors.append(_("All three questions must be different."))
            return False
        return True


# ---------------------------------------------------------------------
# Form: Challenge for verifying identity
# ---------------------------------------------------------------------
class SecurityQuestionChallengeForm(FlaskForm):
    question = StringField(_("Question"), render_kw={"readonly": True})
    answer = StringField(_("Your Answer"), validators=[DataRequired(), Length(min=2, max=255)])
    submit = SubmitField(_("Continue"))
