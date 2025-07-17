"""
# ---------------------------------------------------------------------
# security_questions.py
# app/services/security_questions.py
# Security questions helpers
# ---------------------------------------------------------------------
"""

import hashlib
import hmac

from flask import current_app
from flask_login import current_user

from app.extensions import db
from app.models import SecurityQuestions, User
from app.utils.logging import log_exception_with_traceback, log_info_message


def _get_username():
    try:
        return current_user.username
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------
# Hash security answer
# ---------------------------------------------------------------------
def hash_answer(answer):
    ferret_key = current_app.config["FERRET_KEY"]
    return hmac.new(
        ferret_key.encode(), answer.strip().lower().encode(), hashlib.sha256
    ).hexdigest()


# ---------------------------------------------------------------------
# Save security questions
# ---------------------------------------------------------------------
def save_security_questions(user, form):
    try:
        sq = SecurityQuestions(
            user_id=user.id,
            question_1=form.question_1.data,
            answer_1_hash=hash_answer(form.answer_1.data),
            question_2=form.question_2.data,
            answer_2_hash=hash_answer(form.answer_2.data),
            question_3=form.question_3.data,
            answer_3_hash=hash_answer(form.answer_3.data),
        )
        db.session.add(sq)
        db.session.commit()
        log_info_message(f"Security questions set for user '{user.username}'.")
    except Exception as e:
        log_exception_with_traceback(
            f"Failed to save security questions for user '{user.username}'.", e
        )
        raise


# ---------------------------------------------------------------------
# Verify security answer
# ---------------------------------------------------------------------
def verify_security_answer(user, form):
    if not user or not user.security_questions:
        log_info_message(
            f"Security question check failed: user '{getattr(user, 'username', 'unknown')}' has no questions set."
        )
        return False

    submitted = hash_answer(form.answer.data)
    valid = submitted in {
        user.security_questions.answer_1_hash,
        user.security_questions.answer_2_hash,
        user.security_questions.answer_3_hash,
    }

    log_info_message(
        f"Security question answer {'succeeded' if valid else 'failed'} for user '{user.username}'."
    )
    return valid


# ---------------------------------------------------------------------
# Find user ID
# ---------------------------------------------------------------------
def find_user_by_identifier(identifier):
    if not identifier:
        return None
    return User.query.filter((User.username == identifier) | (User.email == identifier)).first()


# ---------------------------------------------------------------------
# Determine if user has security questions
# ---------------------------------------------------------------------
def user_has_security_questions(user):
    return user and user.security_questions is not None
