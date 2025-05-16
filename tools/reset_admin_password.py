import getpass
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = './data/grylli.db'  # Adjust path if needed

def list_admins(conn):
    cursor = conn.execute("SELECT id, username, email FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    print("Admin users:")
    for admin in admins:
        print(f"ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}")
    return admins

def reset_password(conn, user_id):
    while True:
        pwd1 = getpass.getpass("Enter new password: ")
        pwd2 = getpass.getpass("Confirm new password: ")
        if pwd1 != pwd2:
            print("Passwords do not match, try again.")
        elif len(pwd1) < 8:
            print("Password must be at least 8 characters.")
        else:
            break

    password_hash = generate_password_hash(pwd1)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    print("Password updated successfully.")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    admins = list_admins(conn)
    if not admins:
        print("No admin users found.")
        return

    user_id = input("Enter the ID of the admin user to reset password for: ")
    try:
        user_id = int(user_id)
    except ValueError:
        print("Invalid ID entered.")
        return

    user_ids = [admin[0] for admin in admins]
    if user_id not in user_ids:
        print("User ID not found.")
        return

    reset_password(conn, user_id)

if __name__ == "__main__":
    main()
