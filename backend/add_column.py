import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from sqlalchemy import text

def add_column():
    db = SessionLocal()
    
    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='is_qbo_matched';
        """))
        
        if result.fetchone():
            print("✅ Column 'is_qbo_matched' already exists!")
            return
        
        # Add the column
        print("Adding 'is_qbo_matched' column...")
        db.execute(text("""
            ALTER TABLE transactions 
            ADD COLUMN is_qbo_matched BOOLEAN DEFAULT false;
        """))
        db.commit()
        print("✅ Column added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
