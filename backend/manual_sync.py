import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.transaction_service import TransactionService

def trigger_sync():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    print(f"Syncing transactions for realm: {connection.realm_id}")
    
    service = TransactionService(db, connection)
    service.sync_transactions()
    
    print("✅ Sync complete!")

if __name__ == "__main__":
    trigger_sync()
