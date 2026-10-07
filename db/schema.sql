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

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    tg_id INTEGER,
    service_name TEXT,
    price REAL,
    start_date TEXT,
    end_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_user ON products(tg_id);
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(tg_id);