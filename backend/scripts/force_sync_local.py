import asyncio
import os
import sys
from dotenv import dotenv_values

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Load Env
env_path = os.path.join(backend_dir, ".env")
env_vars = dotenv_values(env_path)
for key, value in env_vars.items():
    os.environ[key] = value

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, Transaction, BankAccount
from app.services.sync_service import SyncService

async def main():
    print("🚀 [Local] Starting Force Sync...")
    
    db = SessionLocal()
    try:
        # User ID from previous scripts
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print(f"❌ No connection found for user {user_id}")
            return

        print(f"🔄 Syncing Realm: {conn.realm_id}")
        
        # Pre-count
        pre_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
        print(f"📊 Pre-sync Tx Count: {pre_count}")
        
        # Verify active accounts
        active_banks = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id, BankAccount.is_active == True).all()
        print(f"✅ Active Accounts: {[f'{b.name} ({b.id})' for b in active_banks]}")
        
        service = SyncService(db, conn)
        await service.sync_transactions()
        
        # Post-count
        post_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
        print(f"📊 Post-sync Tx Count: {post_count}")
        print(f"✅ Sync Complete. Added {post_count - pre_count} new transactions.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
