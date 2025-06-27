"""
# ---------------------------------------------------------------------
# decorators.py
# app/utils/decorators.py
# redirects users who haven’t set their questions
# ---------------------------------------------------------------------
"""

from functools import wraps

from flask import flash, redirect, url_for
from flask_babel import _
from flask_login import current_user


def require_security_questions(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if (
            current_user.is_authenticated
            and not current_user.security_questions_set
            and not request.endpoint.startswith("account.set_security_questions")
        ):
            flash(_("Please set your security questions before using the application."), "warning")
            return redirect(url_for("account.set_security_questions"))
        return view_func(*args, **kwargs)

    return wrapper
