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
        # Databases created before the currency feature don't have the column yet
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)")]
        if "currency" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT '$'")


def save_user(tg_id):
    """Remember a user (does nothing if they already exist)."""
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (tg_id) VALUES (?)", (tg_id,))


def set_currency(tg_id, currency):
    """Save the user's currency sign (creates the user if needed)."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO users (tg_id, currency) VALUES (?, ?)
               ON CONFLICT(tg_id) DO UPDATE SET currency = excluded.currency""",
            (tg_id, currency),
        )


def get_currency(tg_id):
    """The user's currency sign, or $ if they never picked one."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT currency FROM users WHERE tg_id = ?", (tg_id,)
        ).fetchone()
    return row["currency"] if row and row["currency"] else "$"


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
    """One row per product with all its prices added up ("Apple" and "apple" merge)."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT LOWER(product_name) AS product_name, SUM(price) AS price
               FROM products WHERE tg_id = ?
               GROUP BY LOWER(product_name) ORDER BY MIN(id)""",
            (tg_id,),
        ).fetchall()

def get_all_tables():
    """Return {table_name: (column_names, rows)} for every table in the database."""
    with get_conn() as conn:
        names = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        ]
        tables = {}
        for name in names:
            cur = conn.execute(f'SELECT * FROM "{name}"')
            tables[name] = ([c[0] for c in cur.description], cur.fetchall())
        return tables
