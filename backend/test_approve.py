
import os
import sys
import asyncio
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.transaction_service import TransactionService

async def test_approve(tx_id: str):
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if not tx:
            print(f"❌ Transaction {tx_id} not found")
            return

        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
        if not conn:
            print(f"❌ Connection for realm {tx.realm_id} not found")
            return

        print(f"🚀 Testing approval for TX: {tx.description} (ID: {tx.id})")
        print(f"   Category: {tx.suggested_category_name} (ID: {tx.suggested_category_id})")
        print(f"   SyncToken: {tx.sync_token}")
        
        service = TransactionService(db, conn)
        
        # We need to mock the QBO Client call if we don't want to hit live API 
        # OR we can hit it if we want a real test.
        # Let's try to hit it but catch errors.
        try:
            result = await service.approve_transaction(tx_id)
            print(f"✅ Success! Result: {result}")
        except Exception as e:
            print(f"❌ Approval failed with error: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_approve.py <tx_id>")
        sys.exit(1)
        
    tx_id = sys.argv[1]
    asyncio.run(test_approve(tx_id))
