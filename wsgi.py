"""
wsgi.py
WSGI entrypoint for Grylli Flask application.
"""

from flask_migrate import Migrate

from app import create_app
from app.extensions import db      # <-- Make sure db is imported

app = create_app()
migrate = Migrate(app, db)         # <-- This line makes `flask db` work
