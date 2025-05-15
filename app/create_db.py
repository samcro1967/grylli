# ---------------------------------------------------------------------
# create_db.py
# CLI script to initialize the Grylli database
# ---------------------------------------------------------------------

import os
import sqlite3
from app.models import create_tables
from app.utils.logging import log_info_message, log_error_message

# ---------------------------------------------------------------------
# Function: init_db
# ---------------------------------------------------------------------

def init_db():
    """
    Creates the SQLite database and all required tables.
    """
    db_path = os.path.join("instance", "gms.db")
    os.makedirs("instance", exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        log_info_message("Database initialized successfully.")
    except Exception as e:
        log_error_message(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
