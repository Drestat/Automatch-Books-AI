from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.transaction_service import TransactionService
import os

def debug_sync_accounts():
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).first()
        if not connection:
            print("❌ No QBO connection found")
            return
            
        service = TransactionService(db, connection)
        print(f"🔄 Syncing accounts for realm {connection.realm_id}...")
        
        # We'll hijack the print or just look at the DB after
        service.sync_bank_accounts()
        
        # Now list what we have in DB
        accounts = db.query(BankAccount).all()
        print("\n--- Accounts in DB after sync ---")
        for a in accounts:
            print(f"ID: {a.id} | Name: {a.name} | Active: {a.is_active}")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_sync_accounts()
