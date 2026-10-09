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
    conn.execute("PRAGMA secure_delete = ON")  # overwrite deleted data with zeros
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the tables from schema.sql (safe to run every start)."""
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def save_user(tg_id):
    """Remember a user (does nothing if they already exist)."""
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (tg_id) VALUES (?)", (tg_id,))


def add_products(tg_id, items):
    """Insert all items in one transaction and return (first_id, last_id).

    The ids are consecutive because nothing else can write in between.
    """
    with get_conn() as conn:
        ids = [
            conn.execute(
                "INSERT INTO products (tg_id, product_name, price) VALUES (?, ?, ?)",
                (tg_id, i["product_name"], i["price"]),
            ).lastrowid
            for i in items
        ]
    return ids[0], ids[-1]


def delete_products(tg_id, first_id, last_id):
    """Delete the user's products with ids in [first_id, last_id]; return count."""
    with get_conn() as conn:
        return conn.execute(
            "DELETE FROM products WHERE tg_id = ? AND id BETWEEN ? AND ?",
            (tg_id, first_id, last_id),
        ).rowcount


def get_products(tg_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT product_name, price FROM products WHERE tg_id = ? ORDER BY added_at",
            (tg_id,),
        ).fetchall()