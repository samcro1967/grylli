"""
tools/reset_admin_password.py
Path: reset_admin_password.py (relative to project root)
Utility script to reset the password of an admin user in the Grylli SQLite database.
Intended for use by sysadmins if admin account recovery is needed.
"""

# ======================
# Standard Library Imports
# ======================
import getpass
import os
import re
import sqlite3
import sys

from werkzeug.security import generate_password_hash

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# pylint: disable=wrong-import-position
from app import config

DB_PATH = config.DATABASE_PATH

# ======================
# Third-Party Imports
# ======================


# ======================
# Configuration
# ======================
PASSWORD_POLICY = """
Password requirements:
  • Minimum 8 characters
  • At least one uppercase letter
  • At least one lowercase letter
  • At least one number
  • At least one special character (e.g., !@#$%)
"""


# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------
def list_admins(conn):
    """
    Retrieve and print a list of admin users from the database.
    Handles KeyboardInterrupt gracefully.

    Args:
        conn (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        List[Tuple]: List of tuples with (id, username, email) for each admin user,
        or None if interrupted.
    """
    try:
        cursor = conn.execute("SELECT id, username, email FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        print("Admin users:")
        for admin in admins:
            print(f"ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}")
        return admins
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting.")
        return None


# ---------------------------------------------------------------------
def reset_password(conn, user_id):
    """
    Prompt for and update the password for the given admin user ID.
    Handles KeyboardInterrupt gracefully during password prompts.
    """
    print(PASSWORD_POLICY)  # Show password rules before prompting

    try:
        while True:
            pwd1 = getpass.getpass("Enter new password: ")
            pwd2 = getpass.getpass("Confirm new password: ")
            if pwd1 != pwd2:
                print("Passwords do not match, try again.")
            elif not validate_password(pwd1):
                print("Password does not meet requirements, try again.")
            else:
                break
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. No changes made.")
        return

    password_hash = generate_password_hash(pwd1)
    try:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()
        print("Password updated successfully.")
    except sqlite3.Error as e:
        print(f"Error updating password: {e}")


# ---------------------------------------------------------------------
def validate_password(password):
    """
    Validate the password against security requirements.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


# ---------------------------------------------------------------------
# Main Script Logic
# ---------------------------------------------------------------------
def main():
    """
    Main function for admin password reset workflow.
    Gracefully handles KeyboardInterrupt.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Failed to connect to database at {DB_PATH}: {e}")
        return

    admins = list_admins(conn)
    if not admins:
        print("No admin users found.")
        return

    try:
        user_id = input("Enter the ID of the admin user to reset password for: ")
        user_id = int(user_id)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting.")
        return
    except ValueError:
        print("Invalid ID entered.")
        return

    user_ids = [admin[0] for admin in admins]
    if user_id not in user_ids:
        print("User ID not found.")
        return

    reset_password(conn, user_id)


# ---------------------------------------------------------------------
# Script Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting.")
