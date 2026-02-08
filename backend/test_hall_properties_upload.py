import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.transaction_service import TransactionService

async def test_upload():
    db = SessionLocal()
    
    # Find the specific transaction
    tx = db.query(Transaction).filter(Transaction.id == "104").first()
    if not tx:
        print("Transaction 104 not found in DB")
        return
        
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    if not connection:
        print("Connection not found")
        return
        
    service = TransactionService(db, connection)
    
    print(f"Testing receipt upload for Transaction {tx.id} ({tx.payee})")
    print(f"Type: {tx.transaction_type}")
    print(f"Mapped Type: {service._map_to_qbo_attachable_type(tx.transaction_type)}")
    
    try:
        await service._upload_receipt(tx)
        print("✅ SUCCESS (or so it seems, check logs above)")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_upload())
