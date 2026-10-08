CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    profile_name TEXT,
    username TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    tg_id INTEGER,
    product_name TEXT,
    price REAL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_user ON products(tg_id);