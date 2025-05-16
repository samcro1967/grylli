# app/utils/locale.py
from flask import request

def get_locale():
    lang = request.cookies.get("user_locale") or request.accept_languages.best_match(["en", "es", "fr"])
    return lang
