# ---------------------------------------------------------------------
# init_db.py
# Initializes the Grylli SQLite database and creates required tables
# ---------------------------------------------------------------------

import sqlite3
import os
import sys

# Add app path if needed for relative import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import create_tables
from app.utils.logging import log_info_message, log_error_message, log_exception_with_traceback, log_step

# ---------------------------------------------------------------------
# Function: init_db
# ---------------------------------------------------------------------

def init_db(db_path="data/gms.db"):
    """
    Connects to the SQLite database and creates all required tables.

    Args:
        db_path (str): Path to the SQLite database file.
    """
    try:
        log_step("Initializing Grylli database")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to the SQLite database (creates file if it doesn't exist)
        conn = sqlite3.connect(db_path)
        log_info_message(f"Connected to database: {db_path}")

        # Create tables
        create_tables(conn)
        log_info_message("All tables created or verified successfully.")

        conn.close()

    except Exception as e:
        log_exception_with_traceback("Database initialization failed", e)
        sys.exit(1)

# ---------------------------------------------------------------------
# Script Entry Point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
