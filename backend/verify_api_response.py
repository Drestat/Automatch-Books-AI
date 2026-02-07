import modal
import sys
import os

# Add backend to path (assuming this script is run from backend dir)
sys.path.append(os.getcwd())

from modal_app import app, image, secrets

@app.function(image=image, secrets=[secrets])
def verify_api_response_remote():
    """
    Runs inside the cloud container to verify the API logic with full dependencies.
    """
    print("🚀 [Verify] Starting remote verification...")
    from app.core.config import settings
    # DB URL from secrets is injected as env var usually in Modal, or loaded by config
    # settings.DATABASE_URL should have it
    print(f"🔌 [Remote] DB Url Configured: {settings.DATABASE_URL[:15]}...") 
    
    from app.db.session import SessionLocal
    from app.models.qbo import Transaction, QBOConnection
    from app.api.v1.endpoints.transactions import get_transactions, TransactionSchema
    
    db = SessionLocal()
    try:
        conn = db.query(QBOConnection).first()
        if not conn:
            print("❌ No connection found")
            return
        
        realm_id = conn.realm_id
        print(f"🔍 Testing Realm: {realm_id}")
        
        # 1. Fetch All
        txs = get_transactions(realm_id=realm_id, account_ids=None, db=db)
        print(f"✅ Fetched {len(txs)} transactions (No Filter)")
        
        if len(txs) == 0:
            print("❌ No transactions found to test serialization")
            return

        # 2. Test Serialization
        print("🔍 Testing Serialization on first 5 items...")
        try:
            serialized_list = [TransactionSchema.from_orm(t) for t in txs[:5]]
            print(f"✅ Successfully serialized {len(serialized_list)} items")
            print(f"Sample JSON: {serialized_list[0].json()}")
        except Exception as e:
            print(f"❌ Serialization Failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # 3. Test Filter
        acc_id = txs[0].account_id
        print(f"🔍 Testing Filter with Account ID: {acc_id}")
        filtered = get_transactions(realm_id=realm_id, account_ids=str(acc_id), db=db)
        print(f"✅ Filtered Count: {len(filtered)}")
        
        if len(filtered) != len(txs): # Assuming all share same account based on previous check
             print(f"⚠️ Filter count mismatch? Total: {len(txs)}, Filtered: {len(filtered)}")

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    with app.run():
        verify_api_response_remote.remote()
