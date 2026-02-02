"""
Add sync_token column to transactions table
Run with: modal run modal_app.py::add_sync_token_column
"""
import modal
from app.db.session import get_db
from sqlalchemy import text

app = modal.App.lookup("qbo-transactions-app", create_if_missing=False)

@app.function()
def add_sync_token_column():
    """Add sync_token column to transactions table for QBO optimistic locking"""
    print("🔄 Adding sync_token column to transactions table...")
    
    db = next(get_db())
    
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='sync_token'
        """))
        
        if result.fetchone():
            print("✅ Column sync_token already exists")
            return {"status": "success", "message": "Column already exists"}
        
        # Add the column
        db.execute(text("ALTER TABLE transactions ADD COLUMN sync_token VARCHAR"))
        db.commit()
        
        print("✅ Successfully added sync_token column to transactions table")
        return {"status": "success", "message": "Column added successfully"}
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        db.rollback()
        raise
    finally:
        db.close()
