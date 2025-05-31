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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    """
    Script entry point. Creates a minimal Flask app, runs migrations if needed,
    and seeds system config data if necessary.
    """
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(_("Tables currently in DB: %s"), tables)

        if not tables or "system_config" not in tables:
            logger.info(_("Database or system_config table missing. Running migrations now..."))
            try:
                upgrade()
                logger.info(_("Migrations applied successfully."))
            except Exception:
                logger.exception(_("Migration failed."))
                raise

        try:
            seed_system_config_from_env()
            logger.info(_("System config seeded successfully."))
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(_("Error seeding system config."))


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------
# End of file: app/init_db.py
# ---------------------------------------------------------------------
