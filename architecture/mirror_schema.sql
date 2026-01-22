-- Local Mirror Schema for QuickBooks Data

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    date TEXT,
    description TEXT,
    amount REAL,
    currency TEXT,
    account_id TEXT,
    account_name TEXT,
    status TEXT DEFAULT 'unmatched', -- unmatched, matched, categorized
    suggested_category_id TEXT,
    suggested_category_name TEXT,
    reasoning TEXT,
    confidence REAL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    display_name TEXT,
    fully_qualified_name TEXT
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    entity_type TEXT,
    count INTEGER,
    status TEXT
);
