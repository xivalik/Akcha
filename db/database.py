import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Paths: data/bot.db on your PC, the Railway volume when deployed
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


@contextmanager
def get_conn():
    """Open the database, save changes, and always close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you use row["product_name"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the tables from schema.sql (safe to run every start)."""
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def save_user(tg_id, profile_name):
    """Add a new user, or update their names if they already exist."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (tg_id, profile_name) VALUES (?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET
                profile_name = excluded.profile_name
            """,
            (tg_id, profile_name),
        )


def add_product(tg_id, product_name, price):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO products (tg_id, product_name, price) VALUES (?, ?, ?)",
            (tg_id, product_name, price),
        )


def get_products(tg_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT product_name, price FROM products WHERE tg_id = ? ORDER BY added_at",
            (tg_id,),
        ).fetchall()