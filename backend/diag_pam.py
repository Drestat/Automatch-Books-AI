import os
import sys
import json
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def find_pam():
    db = SessionLocal()
    try:
        print("Searching for 'Pam Seitz'...")
        txs = db.query(Transaction).filter(
            Transaction.description.ilike("%Pam Seitz%")
        ).all()
        
        if not txs:
            print("❌ No transactions found matching 'Pam Seitz'")
            return

        for tx in txs:
            print(f"\n" + "="*50)
            print(f"TX ID: {tx.id}")
            print(f"Description: {tx.description}")
            print(f"Amount: {tx.amount}")
            print(f"Status: {tx.status}")
            print(f"Is QBO Matched: {tx.is_qbo_matched}")
            print(f"AI Category: {tx.suggested_category_name} (ID: {tx.suggested_category_id})")
            print(f"SyncToken: {tx.sync_token}")
            print(f"Tags: {tx.tags}")
            print(f"Confidence: {tx.confidence}")
            print(f"Raw Details: {json.dumps(tx.raw_json if tx.raw_json else {}, indent=2)}")
            print("="*50)
            
        from app.models.qbo import QBOConnection
        from app.services.token_service import TokenService
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == txs[0].realm_id).first()
        if conn:
            ts = TokenService(db)
            bal = ts.get_balance(conn.user_id)
            print(f"User Token Balance: {bal}")

    finally:
        db.close()

if __name__ == "__main__":
    find_pam()
