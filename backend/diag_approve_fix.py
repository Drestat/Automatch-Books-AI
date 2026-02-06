
import asyncio
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.transaction_service import TransactionService
from dotenv import load_dotenv

load_dotenv()

async def diag_approve(realm_id, tx_id):
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("Connection not found")
            return
        
        service = TransactionService(db, connection)
        print(f"🚀 Attempting to approve tx {tx_id} for realm {realm_id}...")
        
        try:
            result = await service.approve_transaction(tx_id)
            print(f"✅ Success: {result}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    # From previous check: ('151', 'A1 RENTAL BACKHOE DEPOSIT REFUND', 'pending_approval', 'Expense', '9341456245321396')
    asyncio.run(diag_approve('9341456245321396', '151'))
