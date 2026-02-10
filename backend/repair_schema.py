import os
import sys
from sqlalchemy import text, inspect
from app.db.session import engine

def repair():
    print("🏗️ [repair_schema.py] Starting manual schema repair...")
    
    with engine.begin() as conn:
        inspector = inspect(engine)
        
        # 1. USERS TABLE
        print("Checking 'users' table...")
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'auto_accept_enabled' not in columns:
            print("Adding users.auto_accept_enabled...")
            conn.execute(text("ALTER TABLE users ADD COLUMN auto_accept_enabled BOOLEAN DEFAULT TRUE;"))
        
        # 2. TRANSACTIONS TABLE
        print("Checking 'transactions' table...")
        columns = [c['name'] for c in inspector.get_columns('transactions')]
        
        tx_patches = {
            'vendor_reasoning': 'VARCHAR',
            'category_reasoning': 'VARCHAR',
            'note_reasoning': 'VARCHAR',
            'tax_deduction_note': 'VARCHAR',
            'payee': 'VARCHAR',
            'is_qbo_matched': 'BOOLEAN DEFAULT FALSE',
            'is_excluded': 'BOOLEAN DEFAULT FALSE',
            'forced_review': 'BOOLEAN DEFAULT FALSE',
            'sync_token': 'VARCHAR'
        }
        
        for col, col_type in tx_patches.items():
            if col not in columns:
                print(f"Adding transactions.{col}...")
                conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col} {col_type};"))

        # 3. QBO_CONNECTIONS TABLE
        print("Checking 'qbo_connections' table...")
        columns = [c['name'] for c in inspector.get_columns('qbo_connections')]
        if 'updated_at' not in columns:
            print("Adding qbo_connections.updated_at...")
            conn.execute(text("ALTER TABLE qbo_connections ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();"))

    print("✅ [repair_schema.py] Schema repair complete.")

if __name__ == "__main__":
    # Ensure app module is importable
    sys.path.append(os.getcwd())
    repair()
