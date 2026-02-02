import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diag_unmatched_full():
    db = SessionLocal()
    try:
        # Get several unmatched 'Checking' transactions
        txs = db.query(Transaction).filter(
            Transaction.is_qbo_matched == False,
            Transaction.account_name == "Checking"
        ).limit(5).all()
        
        for tx in txs:
            print(f"\n" + "="*50)
            print(f"TX ID: {tx.id} | Description: {tx.description}")
            print("="*50)
            print(json.dumps(tx.raw_json, indent=2))

    finally:
        db.close()

if __name__ == "__main__":
    diag_unmatched_full()
