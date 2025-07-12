# app/helpers/auth_helpers.py

from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from app.models import User

def generate_password_reset_token(user: User) -> str:
    secret_key = current_app.config["SECRET_KEY"]
    salt = current_app.config["SECURITY_PASSWORD_SALT"]
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(user.email, salt=salt)
