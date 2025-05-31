#!/usr/bin/env python3
"""
tools/dump_db_to_json.py
Dumps the current SQLite database to a JSON file in data/.
"""


import json
import os
import sqlite3
import sys
from datetime import datetime

# ---------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "grylli.db")
# Output file includes timestamp for audit/history
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_PATH = os.path.join(BASE_DIR, "data", f"dump_{TIMESTAMP}.json")


# ---------------------------------------------------------------------
# Function to dump entire DB to JSON
# ---------------------------------------------------------------------
def dump_db_to_json(db_path, out_path):
    """
    Connects to the SQLite database and dumps all user tables to a JSON file.
    Each table is stored as a list of dicts under its table name.
    """
    # Use SQLite connection with row factory for dict-like access
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Gather all non-system table names
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row["name"] for row in cursor.fetchall()]

    db_dump = {}

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = [dict(row) for row in cursor.fetchall()]
        db_dump[table] = rows

    # Write out as pretty-printed JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db_dump, f, indent=2, ensure_ascii=False)

    print(f"✅ Database dumped to {out_path}")


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Defensive: warn and exit if DB not found
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    dump_db_to_json(DB_PATH, OUT_PATH)
