import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", ".tmp/mirror.db")

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        schema_path = "architecture/mirror_schema.sql"
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema)
            print(f"✅ Database initialized at {self.db_path}")

    def upsert_transactions(self, transactions):
        query = """
        INSERT INTO transactions (id, date, description, amount, currency, account_id, account_name, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            date=excluded.date,
            description=excluded.description,
            amount=excluded.amount,
            raw_json=excluded.raw_json
        """
        with self.get_connection() as conn:
            conn.executemany(query, transactions)
            print(f"✅ Upserted {len(transactions)} transactions")

    def get_unmatched_transactions(self):
        query = "SELECT * FROM transactions WHERE status = 'unmatched'"
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    def upsert_categories(self, categories):
        query = "INSERT INTO categories (id, name, type) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, type=excluded.type"
        with self.get_connection() as conn:
            conn.executemany(query, categories)
            print(f"✅ Upserted {len(categories)} categories")

    def upsert_customers(self, customers):
        query = "INSERT INTO customers (id, display_name, fully_qualified_name) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name, fully_qualified_name=excluded.fully_qualified_name"
        with self.get_connection() as conn:
            conn.executemany(query, customers)
            print(f"✅ Upserted {len(customers)} customers")

if __name__ == "__main__":
    db = DBManager()
