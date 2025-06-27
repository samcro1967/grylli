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

from app.extensions import db
from app.models import SecurityQuestions, User


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


# ---------------------------------------------------------------------
# Verify security answer
# ---------------------------------------------------------------------
def verify_security_answer(user, form):
    if not user.security_questions:
        return False

    submitted = hash_answer(form.answer.data)
    return submitted in {
        user.security_questions.answer_1_hash,
        user.security_questions.answer_2_hash,
        user.security_questions.answer_3_hash,
    }


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
