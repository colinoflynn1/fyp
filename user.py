# user.py
from typing import Optional, Dict, Any, List
from db import get_conn
from werkzeug.security import generate_password_hash, check_password_hash



#BASIC CRUD FOR ADMIN PANEL

def add_user(email: str, full_name: str, role: str = "user") -> int:
    """Add a new user (admin-created, no password)."""
    sql = "INSERT INTO users (email, full_name, role) VALUES (%s, %s, %s)"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (email, full_name, role))
        return cur.lastrowid


def update_user(user_id: int, *,
                email: Optional[str] = None,
                full_name: Optional[str] = None,
                role: Optional[str] = None) -> bool:
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
    if not fields:
        return False
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id=%s"
    params.append(user_id)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return cur.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Delete a user by ID."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        return cur.rowcount > 0


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a user by ID (used in Flask-Login)."""
    sql = """
        SELECT id, email, full_name, role, password_hash,
               created_at, updated_at
        FROM users WHERE id=%s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchone()


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
#AUTHENTICATION HELPERS

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by their email."""
    sql = """
        SELECT id, email, full_name, role, password_hash,
               created_at, updated_at
        FROM users WHERE email=%s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (email,))
        return cur.fetchone()


def create_user(email: str, full_name: str, password: str, role: str = "user") -> int:
    """Signup helper: creates a user with hashed password."""
    sql = """
        INSERT INTO users (email, full_name, role, password_hash)
        VALUES (%s, %s, %s, %s)
    """
    pw_hash = generate_password_hash(password)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (email, full_name, role, pw_hash))
        return cur.lastrowid


def set_password(user_id: int, new_password: str) -> None:
    """Change a user's password (used in reset)."""
    sql = "UPDATE users SET password_hash=%s WHERE id=%s"
    pw_hash = generate_password_hash(new_password)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (pw_hash, user_id))


def verify_password(pw_hash: Optional[str], password: str) -> bool:
    """Check if a plain password matches its hash."""
    return bool(pw_hash) and check_password_hash(pw_hash, password)
