"""
# ---------------------------------------------------------------------
# extensions.py
# app/extensions.py
# Flask extension singletons for database and more.
# ---------------------------------------------------------------------
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()