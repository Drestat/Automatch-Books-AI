import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.api.v1.endpoints.transactions import get_transactions

def test_get_transactions():
    db = SessionLocal()
    try:
        # Get a Realm ID
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
        
        realm_id = conn.realm_id
        # We know from previous step that active account is '35' (or similar ID, just need to be sure)
        # Let's just query all first
        print(f"Testing get_transactions for Realm: {realm_id}")
        
        # Mock dependency injection
        # Call the function directly
        txs = get_transactions(realm_id=realm_id, account_ids=None, db=db)
        print(f"Total Txs (No Filter): {len(txs)}")

        # Test with specific account ID if we can find one
        if len(txs) > 0:
            acc_id = txs[0].account_id
            print(f"Testing filter with Account ID: {acc_id}")
            filtered_txs = get_transactions(realm_id=realm_id, account_ids=str(acc_id), db=db)
            print(f"Filtered Txs: {len(filtered_txs)}")

            # Check serialization (pydantic model)
            from app.api.v1.endpoints.transactions import TransactionSchema
            try:
                print("Testing Serialization...")
                serialized = [TransactionSchema.from_orm(t) for t in filtered_txs[:5]]
                print("Serialization Successful. Sample:")
                print(serialized[0].json())
            except Exception as e:
                print(f"Serialization Failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    test_get_transactions()
