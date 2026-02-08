import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.transaction_service import TransactionService

import asyncio

async def trigger_sync():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    print(f"🚀 Triggering full sync for realm: {connection.realm_id}")
    
    from app.services.sync_service import SyncService
    service = SyncService(db, connection)
    await service.sync_all()
    
    print("✅ Full sync complete!")

if __name__ == "__main__":
    asyncio.run(trigger_sync())
