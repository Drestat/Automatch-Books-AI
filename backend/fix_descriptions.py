"""
Data migration to fix existing transaction descriptions.
Extracts vendor name from raw_json and updates description field.
"""
import modal

app = modal.App("qbo-sync-engine")

image = (
    modal.Image.debian_slim(python_version="3.9")
    .pip_install([
        "fastapi==0.115.6",
        "uvicorn[standard]==0.34.0",
        "sqlalchemy==2.0.36",
        "psycopg2-binary==2.9.10",
        "pydantic-settings==2.7.0",
    ])
)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("qbo-secrets")],
    timeout=600
)
def fix_transaction_descriptions():
    """Fix existing transaction descriptions by extracting vendor from raw_json"""
    import os
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get all transactions with raw_json
        result = db.execute(text("""
            SELECT id, description, note, raw_json 
            FROM transactions 
            WHERE raw_json IS NOT NULL
        """))
        
        transactions = result.fetchall()
        print(f"Found {len(transactions)} transactions to process")
        
        updated_count = 0
        for tx in transactions:
            tx_id, old_desc, note, raw_json = tx
            
            # Extract vendor name from raw_json
            vendor_name = None
            if 'EntityRef' in raw_json:
                vendor_name = raw_json['EntityRef'].get('name')
            elif 'VendorRef' in raw_json:
                vendor_name = raw_json['VendorRef'].get('name')
            
            # Fallback to Line description
            if not vendor_name and 'Line' in raw_json and len(raw_json['Line']) > 0:
                vendor_name = raw_json['Line'][0].get('Description')
            
            new_desc = vendor_name if vendor_name else "Uncategorized Expense"
            
            # Extract payee
            payee_name = None
            if 'EntityRef' in raw_json:
                payee_name = raw_json['EntityRef'].get('name')
            elif 'VendorRef' in raw_json:
                payee_name = raw_json['VendorRef'].get('name')
            
            # Only update if description changed
            if new_desc != old_desc:
                db.execute(text("""
                    UPDATE transactions 
                    SET description = :new_desc, payee = :payee
                    WHERE id = :tx_id
                """), {"new_desc": new_desc, "payee": payee_name, "tx_id": tx_id})
                updated_count += 1
                
                if updated_count <= 5:  # Show first 5 examples
                    print(f"  Updated {tx_id}: '{old_desc}' -> '{new_desc}'")
        
        db.commit()
        print(f"\n✅ Updated {updated_count} transactions")
        return {"updated": updated_count, "total": len(transactions)}
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

@app.local_entrypoint()
def main():
    result = fix_transaction_descriptions.remote()
    print(f"\nMigration complete: {result}")
