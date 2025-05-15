# ---------------------------------------------------------------------
# db.py
# SQLite connection management for Grylli using Flask context
# ---------------------------------------------------------------------

import sqlite3
from flask import g, current_app

def get_db():
    """
    Retrieves the SQLite connection for the current request context.

    Returns:
        sqlite3.Connection: The active database connection.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """
    Closes the database connection at the end of the request lifecycle.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
