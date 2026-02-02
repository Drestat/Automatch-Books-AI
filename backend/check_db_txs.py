import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection

def check_db_transactions():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    realm_id = connection.realm_id
    print(f"Checking realm: {realm_id}\n")
    
    # Get all transactions
    all_txs = db.query(Transaction).filter(Transaction.realm_id == realm_id).all()
    print(f"Total transactions in DB: {len(all_txs)}\n")
    
    if len(all_txs) == 0:
        print("❌ NO TRANSACTIONS FOUND IN DATABASE!")
        print("This means the sync didn't save anything to the database.")
        return
    
    # Group by status
    by_status = {}
    for tx in all_txs:
        status = tx.status or 'null'
        by_status[status] = by_status.get(status, 0) + 1
    
    print("Transactions by status:")
    for status, count in by_status.items():
        print(f"  {status}: {count}")
    
    print("\nSample transactions:")
    for tx in all_txs[:5]:
        print(f"  ID: {tx.id}, Date: {tx.date}, Status: {tx.status}, Account: {tx.account_name}")
        print(f"    Description: {tx.description}")
        print(f"    is_qbo_matched: {tx.is_qbo_matched}")
        print()

if __name__ == "__main__":
    check_db_transactions()
