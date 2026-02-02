"""
Simple migration script to add sync_token column to transactions table
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/qbo_transactions")

def main():
    print("🔄 Adding sync_token column to transactions table...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='sync_token'
        """))
        
        if result.fetchone():
            print("✅ Column sync_token already exists")
            return
        
        # Add the column
        conn.execute(text("ALTER TABLE transactions ADD COLUMN sync_token VARCHAR"))
        conn.commit()
        
        print("✅ Successfully added sync_token column to transactions table")

if __name__ == "__main__":
    main()
