-- PostgreSQL Schema for Multi-tenant QBO Mirror

-- Users table (SaaS Auth)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- QuickBooks Connections
CREATE TABLE IF NOT EXISTS qbo_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    realm_id TEXT UNIQUE NOT NULL,
    refresh_token TEXT NOT NULL,
    access_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mirrored Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY, -- QBO Transaction Id
    realm_id TEXT REFERENCES qbo_connections(realm_id) ON DELETE CASCADE,
    date DATE,
    description TEXT,
    amount DECIMAL(15, 2),
    currency TEXT,
    account_id TEXT,
    account_name TEXT,
    status TEXT DEFAULT 'unmatched',
    suggested_category_id TEXT,
    suggested_category_name TEXT,
    reasoning TEXT,
    confidence DECIMAL(3, 2),
    raw_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Categories (Accounts)
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    realm_id TEXT REFERENCES qbo_connections(realm_id) ON DELETE CASCADE,
    name TEXT,
    type TEXT,
    description TEXT
);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    realm_id TEXT REFERENCES qbo_connections(realm_id) ON DELETE CASCADE,
    display_name TEXT,
    fully_qualified_name TEXT
);
