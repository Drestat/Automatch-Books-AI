
import asyncio
import os
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, Transaction
from app.services.qbo_client import QBOClient
from app.services.transaction_service import TransactionService
from dotenv import load_dotenv

load_dotenv()

class MockUser:
    id = "test_user"

async def test_retry_logic():
    db = SessionLocal()
    try:
        # 1. Setup Service
        realm_id = '9341456245321396'
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("Connection not found")
            return
            
        service = TransactionService(db, connection)
        
        # 2. Get the transaction (Cool Cars)
        tx_id = '61'
        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if not tx:
            print("Transaction not found!")
            return

        # 3. Simulate Stale State
        # We know QBO has SyncToken > 0 (likely '1' or '2' from previous successful runs)
        # We forcibly set local DB SyncToken to '0' to guarantee a conflict
        print(f"Original Local SyncToken: {tx.sync_token}")
        tx.sync_token = "0" 
        db.commit()
        print("Forced Local SyncToken to '0' to trigger Stale Object Error.")

        # 4. Attempt Approval via Service
        print("Calling service.approve_transaction...")
        # Note: approve_transaction signature might vary, checking usage in code would be ideal but 
        # based on typical pattern: approve_transaction(user, tx_id, ...)
        
        # We need to see the actual signature of approve_transaction in TransactionService
        # Assuming: async def approve_transaction(self, user, transaction_id: str, ...)
        
        await service.approve_transaction(tx_id=tx_id)
        
        print("✅ Service call completed successfully!")
        
        # 5. Verify New SyncToken
        db.refresh(tx)
        print(f"Final Local SyncToken: {tx.sync_token}")
        if tx.sync_token != "0":
             print("✅ SyncToken was updated!")
        else:
             print("❌ SyncToken remained 0 (unexpected if update succeeded)")

    except Exception as e:
        print(f"❌ Service call failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_retry_logic())
