import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from sqlalchemy import func

def check_tx_counts():
    db = SessionLocal()
    try:
        # Get a Realm ID
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
        
        realm_id = conn.realm_id
        print(f"Checking Realm: {realm_id}")

        # Total count
        total = db.query(Transaction).filter(Transaction.realm_id == realm_id).count()
        print(f"Total Transactions: {total}")

        # Count by status
        status_counts = db.query(
            Transaction.status, func.count(Transaction.status)
        ).filter(
            Transaction.realm_id == realm_id
        ).group_by(Transaction.status).all()

        print("--- Counts by Status ---")
        for status, count in status_counts:
            print(f"{status}: {count}")

        # Check for null status
        null_status = db.query(Transaction).filter(
            Transaction.realm_id == realm_id, 
            Transaction.status == None
        ).count()
        print(f"Null Status: {null_status}")

    finally:
        db.close()

if __name__ == "__main__":
    check_tx_counts()
