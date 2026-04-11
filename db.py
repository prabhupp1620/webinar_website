import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()


def get_db():
    """Return a new PyMySQL connection using env credentials."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        db=os.getenv("DB_NAME", "webinar_db"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def query(sql, args=None, one=False):
    """Execute a SELECT and return dict rows."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def execute(sql, args=None):
    """Execute INSERT / UPDATE / DELETE, return lastrowid."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()
