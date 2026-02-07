import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(os.getcwd())
from app.core.config import settings

def check_columns():
    engine = create_engine(settings.DATABASE_URL)
    print(f"🔌 [Local] Connecting to Host: {engine.url.host}")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='transactions'
        """))
        for row in result.fetchall():
            print(f"Column: {row[0]} | Type: {row[1]}")
        
        if "potential_duplicate_id" in columns:
            print("✅ potential_duplicate_id exists")
        else:
            print("❌ potential_duplicate_id MISSING")

        if "duplicate_confidence" in columns:
            print("✅ duplicate_confidence exists")
        else:
            print("❌ duplicate_confidence MISSING")

if __name__ == "__main__":
    check_columns()
