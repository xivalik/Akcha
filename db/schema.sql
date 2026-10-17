CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY
);

-- product_name is always the short English name ("milk", not "maito")
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    tg_id INTEGER,
    product_name TEXT,
    price INTEGER,
    added_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_user ON products(tg_id);

