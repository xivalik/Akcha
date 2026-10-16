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


def save_product(tg_id, name, price):
    """Save one product for the user and return its id."""
    with get_conn() as conn:
        return conn.execute(
            "INSERT INTO products (tg_id, product_name, price) VALUES (?, ?, ?)",
            (tg_id, name, price),
        ).lastrowid


def delete_product(tg_id, product_id):
    """Delete one of the user's products; False if it was already deleted."""
    with get_conn() as conn:
        deleted = conn.execute(
            "DELETE FROM products WHERE tg_id = ? AND id = ?", (tg_id, product_id)
        ).rowcount
    return deleted > 0


def get_products(tg_id):
    """One row per product with all its prices added up ("Apple" and "apple" merge),
    most expensive first."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT LOWER(product_name) AS product_name, SUM(price) AS price
               FROM products WHERE tg_id = ?
               GROUP BY LOWER(product_name) ORDER BY SUM(price) DESC, MIN(id)""",
            (tg_id,),
        ).fetchall()


def get_all_tables():
    """Return {table_name: (column_names, rows)} for every table in the database."""
    with get_conn() as conn:
        table_names = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        ]
        tables = {}
        for table_name in table_names:
            cursor = conn.execute(f'SELECT * FROM "{table_name}"')
            columns = [column[0] for column in cursor.description]
            tables[table_name] = (columns, cursor.fetchall())
        return tables
