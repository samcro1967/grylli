# ---------------------------------------------------------------------
# models.py
# SQLite schema definitions and database utilities for Grylli
# ---------------------------------------------------------------------

import sqlite3

# ---------------------------------------------------------------------
# Function: create_tables
# Creates all required tables if they do not exist.
# ---------------------------------------------------------------------

def create_tables(conn: sqlite3.Connection):
    """
    Creates the initial set of tables for the Grylli database.
    
    Args:
        conn (sqlite3.Connection): SQLite database connection.
    """
    cursor = conn.cursor()

    # -----------------------------------------------------------------
    # Table: users
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,           -- Add this line
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
            date_created TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------------------
    # Table: messages
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            encrypted INTEGER DEFAULT 1,
            delivery_timeout_minutes INTEGER DEFAULT 1440,
            last_checkin TEXT,
            date_created TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # -----------------------------------------------------------------
    # Table: destinations
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('apprise', 'webhook')),
            target TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id)
        );
    """)

    # -----------------------------------------------------------------
    # Table: attachments
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            encrypted INTEGER DEFAULT 1,
            file_size_bytes INTEGER,
            date_uploaded TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages(id)
        );
    """)

    # -----------------------------------------------------------------
    # Table: confirmations
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confirmations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            checkin_time TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id)
        );
    """)

    # -----------------------------------------------------------------
    # Table: schema_version
    # -----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );
    """)

    conn.commit()

class User:
    def __init__(self, id_, username, email, password_hash, role):
        self.id = id_
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_username(db, username):
        row = db.execute(
            "SELECT id, username, email, password_hash, role FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return None
        return User(row['id'], row['username'], row['email'], row['password_hash'], row['role'])

    @staticmethod
    def get_by_id(db, user_id):
        row = db.execute(
            "SELECT id, username, email, password_hash, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        return User(row['id'], row['username'], row['email'], row['password_hash'], row['role'])

    # Flask-Login properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True  # Or implement your own active logic

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
