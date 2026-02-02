"""
Live verification script to compare what's in our DB vs what QBO actually shows
"""
import modal
import os
from dotenv import dotenv_values
from modal import Image

# Load env vars
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

image = Image.debian_slim(python_version="3.9").pip_install(
    "sqlalchemy",
    "psycopg2-binary",
    "requests",
    "oauthlib",
    "requests-oauthlib",
    "intuit-oauth",
    "python-dotenv",
    "pydantic-settings"
).add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")

app = modal.App("verify-live-state")

secrets = modal.Secret.from_dict({
    "POSTGRES_USER": env_vars.get("POSTGRES_USER", ""),
    "POSTGRES_PASSWORD": env_vars.get("POSTGRES_PASSWORD", ""),
    "POSTGRES_HOST": env_vars.get("POSTGRES_HOST", ""),
    "POSTGRES_DB": env_vars.get("POSTGRES_DB", ""),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
})

@app.function(image=image, secrets=[secrets])
def verify_mastercard_state():
    """Check what's actually in our database vs what QBO returns"""
    from app.services.qbo_client import QBOClient
    from app.db.session import get_db
    from app.models.qbo import QBOConnection, Transaction
    import json
    
    db = next(get_db())
    try:
        connection = db.query(QBOConnection).first()
        client = QBOClient(db, connection)
        
        print("\n" + "="*120)
        print("LIVE STATE VERIFICATION: MASTERCARD (ID 41)")
        print("="*120)
        
        # 1. Check what's in our DATABASE
        print("\n📊 DATABASE STATE (What the app is showing):")
        db_txns = db.query(Transaction).filter(Transaction.account_id == "41").all()
        print(f"Total transactions in DB: {len(db_txns)}")
        
        categorized_count = sum(1 for t in db_txns if t.is_qbo_matched)
        review_count = sum(1 for t in db_txns if not t.is_qbo_matched)
        
        print(f"  - Categorized: {categorized_count}")
        print(f"  - For Review: {review_count}")
        
        print("\nCategorized items:")
        for t in db_txns:
            if t.is_qbo_matched:
                print(f"  ID {t.qbo_id}: {t.description} | ${t.amount} | Date: {t.date}")
        
        print("\nFor Review items:")
        for t in db_txns:
            if not t.is_qbo_matched:
                print(f"  ID {t.qbo_id}: {t.description} | ${t.amount} | Date: {t.date}")
        
        # 2. Check what QBO ACTUALLY has
        print("\n" + "="*120)
        print("QBO RAW DATA (What should be showing):")
        print("="*120)
        
        res = client.query("SELECT * FROM Purchase WHERE AccountRef = '41'")
        purchases = res.get("QueryResponse", {}).get("Purchase", [])
        
        print(f"\nTotal Purchase items for Mastercard: {len(purchases)}")
        
        # Apply our filter logic manually to see what SHOULD pass
        passed = []
        filtered = []
        
        for p in purchases:
            pid = p.get("Id")
            amt = p.get("TotalAmt")
            date = p.get("TxnDate")
            entity_ref = p.get("EntityRef")
            private_note = p.get("PrivateNote")
            doc_number = p.get("DocNumber")
            metadata = p.get("MetaData", {})
            create_time = metadata.get("CreateTime", "")
            
            # Check our filter criteria
            has_payee = entity_ref is not None
            has_note = private_note and len(private_note.strip()) > 0
            is_debit = doc_number and doc_number.lower() == "debit"
            
            # Check if created today (simplified - just check if today's date)
            is_recent = "2026-02-02" in create_time if create_time else False
            
            has_bank_signal = has_payee or has_note or is_debit or is_recent
            
            item_info = {
                "id": pid,
                "date": date,
                "amount": amt,
                "payee": entity_ref.get("name") if entity_ref else "NO PAYEE",
                "note": private_note or "NO NOTE",
                "created": create_time,
                "has_signal": has_bank_signal
            }
            
            if has_bank_signal:
                passed.append(item_info)
            else:
                filtered.append(item_info)
        
        print(f"\n✅ Items that PASS filter (should show in app): {len(passed)}")
        for item in passed:
            print(f"  ID {item['id']}: {item['payee']} | ${item['amount']} | Created: {item['created']}")
        
        print(f"\n❌ Items that FAIL filter (should be hidden): {len(filtered)}")
        for item in filtered:
            print(f"  ID {item['id']}: {item['payee']} | ${item['amount']} | Note: {item['note'][:30] if item['note'] != 'NO NOTE' else 'NO NOTE'}")
        
        print("\n" + "="*120)
        print("DISCREPANCY ANALYSIS:")
        print("="*120)
        print(f"Expected in app (after filter): {len(passed)}")
        print(f"Actually in app (from DB): {len(db_txns)}")
        print(f"Difference: {len(db_txns) - len(passed)}")
        
        if len(db_txns) != len(passed):
            print("\n⚠️  MISMATCH DETECTED - The filter is NOT being applied during sync!")
            print("This means the 'continue' logic in sync_transactions is not working.")
        
    finally:
        db.close()
