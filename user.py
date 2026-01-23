# user.py
from typing import Optional, Dict, Any, List
from contextlib import suppress
from db import get_conn
from werkzeug.security import generate_password_hash, check_password_hash


# Reference: Based on Similar pattern to goals.py ensure_goal_tables 
# Ensures the users table has notification preference columns
def ensure_user_table():
    """Ensure users table has notification preference columns."""
    with get_conn() as conn, conn.cursor() as cur:
        # Add email_notifications column if it doesn't exist
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE
                """
            )
        # Add dashboard_notifications column if it doesn't exist
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN dashboard_notifications BOOLEAN DEFAULT TRUE
                """
            )


# Call on import to ensure columns exist
ensure_user_table()


# Reference: Based on MySQL Documentation - INSERT statement
# https://dev.mysql.com/doc/refman/8.0/en/insert.html
# BASIC CRUD FOR ADMIN PANEL

def add_user(email: str, full_name: str, role: str = "user") -> int:
    """Add a new user (admin-created, no password)."""
    sql = "INSERT INTO users (email, full_name, role) VALUES (%s, %s, %s)"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (email, full_name, role))
        return cur.lastrowid


# Reference: Based on MySQL Documentation - UPDATE statement
# https://dev.mysql.com/doc/refman/8.0/en/update.html
# Dynamic SQL construction pattern adapted from Flask-SQLAlchemy patterns
def update_user(user_id: int, *,
                email: Optional[str] = None,
                full_name: Optional[str] = None,
                role: Optional[str] = None,
                email_notifications: Optional[bool] = None,
                dashboard_notifications: Optional[bool] = None) -> bool:
    """Update an existing user's details."""
    fields, params = [], []
    if email is not None:
        fields.append("email=%s")
        params.append(email)
    if full_name is not None:
        fields.append("full_name=%s")
        params.append(full_name)
    if role is not None:
        fields.append("role=%s")
        params.append(role)
    if email_notifications is not None:
        fields.append("email_notifications=%s")
        params.append(email_notifications)
    if dashboard_notifications is not None:
        fields.append("dashboard_notifications=%s")
        params.append(dashboard_notifications)
    if not fields:
        return False
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id=%s"
    params.append(user_id)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return cur.rowcount > 0


# Reference: Based on MySQL Documentation - DELETE statement
# https://dev.mysql.com/doc/refman/8.0/en/delete.html
def delete_user(user_id: int) -> bool:
    """Delete a user by ID."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        return cur.rowcount > 0


# Reference: Based on MySQL Documentation - SELECT statement
# https://dev.mysql.com/doc/refman/8.0/en/select.html
# Used by Flask-Login user_loader callback
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a user by ID (used in Flask-Login)."""
    sql = """
        SELECT id, email, full_name, role, password_hash,
               email_notifications, dashboard_notifications,
               created_at, updated_at
        FROM users WHERE id=%s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchone()


# Reference: Based on MySQL Documentation - SELECT with LIMIT
# https://dev.mysql.com/doc/refman/8.0/en/select.html#select-limit
# Admin table listing pattern
def list_users(limit: int = 200) -> List[Dict[str, Any]]:
    """Return all users for admin table."""
    sql = """
        SELECT id, email, full_name, role, created_at, updated_at
        FROM users ORDER BY id DESC LIMIT %s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (limit,))
        return cur.fetchall()


# ----------------------------
# Reference: Based on MySQL Documentation - SELECT with WHERE clause
# https://dev.mysql.com/doc/refman/8.0/en/select.html#select-where
#AUTHENTICATION HELPERS

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by their email."""
    sql = """
        SELECT id, email, full_name, role, password_hash,
               email_notifications, dashboard_notifications,
               created_at, updated_at
        FROM users WHERE email=%s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (email,))
        return cur.fetchone()


# Reference: Based on Werkzeug Security Documentation - Password Hashing
# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
# MySQL INSERT pattern for user creation
def create_user(email: str, full_name: str, password: str, role: str = "user") -> int:
    """Signup helper: creates a user with hashed password."""
    sql = """
        INSERT INTO users (email, full_name, role, password_hash, 
                          email_notifications, dashboard_notifications)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    pw_hash = generate_password_hash(password)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (email, full_name, role, pw_hash, True, True))
        return cur.lastrowid


# Reference: Based on Werkzeug Security Documentation - Password Hashing
# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
# MySQL UPDATE pattern for password changes
def set_password(user_id: int, new_password: str) -> None:
    """Change a user's password (used in reset)."""
    sql = "UPDATE users SET password_hash=%s WHERE id=%s"
    pw_hash = generate_password_hash(new_password)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (pw_hash, user_id))


# Reference: Based on Werkzeug Security Documentation - Password Checking
# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.check_password_hash
def verify_password(pw_hash: Optional[str], password: str) -> bool:
    """Check if a plain password matches its hash."""
    return bool(pw_hash) and check_password_hash(pw_hash, password)
