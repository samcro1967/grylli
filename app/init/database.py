"""
# ---------------------------------------------------------------------
# database.py
# app/init/database.py
# Database setup, migration, and seeding for Flask application factory.
# ---------------------------------------------------------------------
"""

import os

from flask_migrate import Migrate, upgrade
from sqlalchemy import inspect, text

from app.extensions import db
from app.services.settings import seed_system_config_from_env
from app.utils.logging import (
    log_debug_message,
    log_error_message,
    log_exception_with_traceback,
    log_info_message,
)


def setup_database(app):
    """
    Setup the database, run initial migrations, and seed config if needed.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # Database Setup
    # -------------------------------------------
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    log_info_message(("DB URI: ") + db_uri)
    db.init_app(app)

    # -------------------------------------------
    # Initial DB Migration & Seeding (if needed)
    # -------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        log_debug_message(f"Tables currently in DB: {tables}")

        migrations_dir = "./migrations"
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "grylli.db")
        Migrate(app, db, directory=migrations_dir)

        if not tables or "system_config" not in tables:
            log_info_message("Database or system_config table missing. Running migrations now...")
            if os.path.exists(migrations_dir):
                try:
                    upgrade()
                    log_info_message("✅ Migrations applied successfully.")
                except Exception as e:
                    log_error_message("❌ Migration failed.")
                    log_exception_with_traceback("Migration error", exception=e)
                    raise
            else:
                log_info_message("🛑 Skipping migrations — migrations folder or DB not found.")

        # Seed system config from env if needed
        if "system_config" in tables and not os.environ.get("SKIP_SEEDING"):
            try:
                seed_system_config_from_env()
                log_info_message("System config seeded successfully.")
            except Exception as e:  # pylint: disable=broad-exception-caught
                log_error_message("Error seeding system config")
                log_exception_with_traceback("Seeding error", exception=e)
        else:
            log_info_message(
                "⏭️ Skipping seeding — system_config table not found yet or SKIP_SEEDING is set."
            )
