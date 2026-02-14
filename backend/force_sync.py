import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.sync_service import SyncService
from dotenv import load_dotenv

load_dotenv()

async def force_sync():
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print(f"❌ No connection found for user {user_id}")
            return

        print(f"🚀 Force Syncing Realm: {conn.realm_id}")
        service = SyncService(db, conn)
        await service.sync_transactions()
        print("✅ Sync Complete")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(force_sync())
