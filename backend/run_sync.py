import os
import sys
import asyncio
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.transaction_service import TransactionService

async def run_sync():
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).first()
        if not connection:
            print("No QBO Connection found.")
            return

        print(f"Starting Sync for Realm: {connection.realm_id}")
        service = TransactionService(db, connection)
        
        # We only need transactions, but sync_transactions checks for active accounts.
        # We just enabled Checking, so it should work.
        await service.sync_transactions()
        
        print("✅ Sync Completed.")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_sync())
