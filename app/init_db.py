# ---------------------------------------------------------------------
# init_db.py
# Minimal Flask app factory and script to run DB migrations and seed data
# No blueprints or server startup here
# ---------------------------------------------------------------------

from flask import Flask
from flask_migrate import upgrade
from app.models import db
from app.services.settings import seed_system_config_from_env
from sqlalchemy import inspect
from flask import Flask
from flask_migrate import upgrade
from app.extensions import db
from app.services.settings import seed_system_config_from_env
from sqlalchemy import inspect
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(os.path.join(app.root_path, "config.py"))

    # Initialize DB and migrations only
    db.init_app(app)

    return app

def main():
    app = create_app()
    with app.app_context():
        # Check if DB or required tables exist:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables currently in DB: {tables}")

        # Run migrations if needed
        if not tables or "system_config" not in tables:
            logger.info("Database or system_config table missing. Running migrations now...")
            try:
                upgrade()
                logger.info("Migrations applied successfully.")
            except Exception as e:
                logger.error("Migration failed.")
                raise

        # Seed system config
        try:
            seed_system_config_from_env()
            logger.info("System config seeded successfully.")
        except Exception as e:
            logger.error(f"Error seeding system config: {e}")
            # Optional: raise or continue

if __name__ == "__main__":
    main()
