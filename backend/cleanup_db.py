"""
Quick script to manually clean up QBO connections from the database.
Run this when you need to force a fresh connection.
"""
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, Transaction, BankAccount, SyncLog
from app.models.user import User

def cleanup_all_connections():
    db = SessionLocal()
    try:
        # Get all connections
        connections = db.query(QBOConnection).all()
        print(f"Found {len(connections)} QBO connections")
        
        for conn in connections:
            print(f"\n🔍 Connection: realm_id={conn.realm_id}, user_id={conn.user_id}")
            
            # Delete associated data
            tx_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).delete()
            acc_count = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id).delete()
            log_count = db.query(SyncLog).filter(SyncLog.realm_id == conn.realm_id).delete()
            
            print(f"  🗑️  Deleted: {tx_count} transactions, {acc_count} accounts, {log_count} logs")
            
            # Delete connection
            db.delete(conn)
            print(f"  ✅ Deleted connection")
        
        db.commit()
        print(f"\n✅ Cleanup complete! Deleted {len(connections)} connections.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧹 Starting database cleanup...")
    cleanup_all_connections()
