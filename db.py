# db.py
import os
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

# Always load the .env that sits beside this file (works regardless of working dir)
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

DB_PASS = os.getenv("DB_PASS", "")
if not DB_PASS:
    raise RuntimeError(
        "DB_PASS is empty. Put your MySQL password in the .env file next to db.py."
    )

CONF = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "fyp_app"),
    "user": os.getenv("DB_USER", "fyp_user"),
    "password": DB_PASS,
    "autocommit": False,
}

@contextmanager
def get_conn():
    """
    Usage:
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT 1")
                print(cur.fetchone())
    """
    conn = None
    try:
        conn = mysql.connector.connect(**CONF)
        yield conn
        conn.commit()
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise RuntimeError("DB auth failed (check DB_USER/DB_PASS in .env)") from e
        elif e.errno == errorcode.ER_BAD_DB_ERROR:
            raise RuntimeError("Database does not exist (check DB_NAME in .env)") from e
        else:
            raise
    finally:
        if conn:
            conn.close()
