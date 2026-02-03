import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection

db = SessionLocal()
try:
    # Get the latest connection
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("❌ No connection found")
        sys.exit(1)
    
    realm_id = connection.realm_id
    print(f"Checking realm: {realm_id}\n")
    
    # Count all transactions
    total_txs = db.query(Transaction).filter(Transaction.realm_id == realm_id).count()
    print(f"Total transactions in DB: {total_txs}")
    
    if total_txs == 0:
        print("❌ NO TRANSACTIONS IN DATABASE!")
        print("This means the sync deleted all transactions or failed to save them.")
    else:
        print(f"✅ {total_txs} transactions found in database\n")
        
        # Check a sample transaction
        sample = db.query(Transaction).filter(Transaction.realm_id == realm_id).first()
        print("Sample transaction:")
        print(f"  ID: {sample.id}")
        print(f"  Description: {sample.description}")
        print(f"  Amount: {sample.amount}")
        print(f"  Payee: {sample.payee}")
        print(f"  Note: {sample.note}")
        print(f"  is_qbo_matched: {sample.is_qbo_matched}")
        print(f"  is_excluded: {sample.is_excluded}")
        
finally:
    db.close()
