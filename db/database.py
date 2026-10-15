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
# 1: short shopping-list names ("energy drink", not "energy drink 0,473l can")
# 2: products are saved under their English name; no translations table
ENGLISH_VERSION = 2


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
        # Older databases have a currency or language column; the bot is English only now
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)")]
        for column in ("currency", "language"):
            if column in columns:
                conn.execute(f"ALTER TABLE users DROP COLUMN {column}")


def old_product_names():
    """For databases from before products were saved in English: ([every product name],
    {name: English name} already known from the old translations table).

    None once all products are in English.
    """
    with get_conn() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version >= ENGLISH_VERSION:
            return None
        names = [
            r["product_name"]
            for r in conn.execute("SELECT DISTINCT product_name FROM products")
        ]
        has_translations = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'translations'"
        ).fetchone()
        # Only version 1 translations follow the current naming rules
        known = {}
        if has_translations and version >= 1:
            known = {
                r["product_name"]: r["translated"]
                for r in conn.execute(
                    "SELECT product_name, translated FROM translations WHERE language = 'en'"
                )
            }
    # The translations were saved under the lowercase name
    return names, {n: known[n.lower()] for n in names if n.lower() in known}


def rename_products(names):
    """Rename products {old name: English name} and mark the database as all English."""
    with get_conn() as conn:
        # By id, so a new name that is also an old name isn't renamed twice
        rows = conn.execute("SELECT id, product_name FROM products").fetchall()
        conn.executemany(
            "UPDATE products SET product_name = ? WHERE id = ?",
            [(names[r["product_name"]], r["id"]) for r in rows if r["product_name"] in names],
        )
        conn.execute("DROP TABLE IF EXISTS translations")
        conn.execute(f"PRAGMA user_version = {ENGLISH_VERSION}")


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

