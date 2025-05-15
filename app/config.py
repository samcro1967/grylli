# app/config.py

import os

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///grylli.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
