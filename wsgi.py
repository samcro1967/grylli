"""
wsgi.py
WSGI entrypoint for Grylli Flask application.
"""

from app import create_app
from app.extensions import db      # <-- Make sure db is imported
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)         # <-- This line makes `flask db` work
