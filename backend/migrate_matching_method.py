import os
import sys

# Ensure backend root is in path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from sqlalchemy import text

def add_matching_method():
    db = SessionLocal()
    
    try:
        # Check if column exists
        # Note: postgres-specific check. Use table_name='transactions'
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='matching_method';
        """))
        
        if result.fetchone():
            print("✅ Column 'matching_method' already exists!")
            return
        
        # Add the column
        # Default value matches model Column(String, default='none')
        print("Adding 'matching_method' column...")
        db.execute(text("""
            ALTER TABLE transactions 
            ADD COLUMN matching_method VARCHAR DEFAULT 'none';
        """))
        db.commit()
        print("✅ Column added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_matching_method()
