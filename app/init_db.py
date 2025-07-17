"""
# ---------------------------------------------------------------------
# init_db.py
# app/init_db.py
# Minimal Flask app factory and script to run DB migrations and seed data.
# ---------------------------------------------------------------------
"""

import logging
import os

from flask import Flask
from flask_babel import _
from flask_migrate import upgrade
from sqlalchemy import inspect

from app.extensions import db
from app.services.settings import seed_system_config_from_env
from app.utils.logging import log_exception_with_traceback, log_info_message


# ---------------------------------------------------------------------
# create_app
# ---------------------------------------------------------------------
def create_app():
    """
    Minimal Flask app factory that initializes the database and migrations.
    Used by this script to run migrations and seed data without starting the server.

    Returns:
        Flask app instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    db.init_app(app)
    return app


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------
def main():
    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            log_info_message(f"Tables currently in DB: {tables}")

            if not tables or "system_config" not in tables:
                log_info_message(
                    "Database or system_config table missing. Running migrations now..."
                )
                upgrade()
                log_info_message("Migrations applied successfully.")

            seed_system_config_from_env()
            log_info_message("System config seeded successfully.")

        except Exception as e:
            log_exception_with_traceback("init_db script failed", e)
            raise


if __name__ == "__main__":
    main()
