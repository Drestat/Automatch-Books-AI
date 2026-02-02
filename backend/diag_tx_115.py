import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diag_transactions_full():
    db = SessionLocal()
    try:
        # Get specific transaction (Hicks Hardware)
        tx = db.query(Transaction).filter(Transaction.id == "115").first()
        
        if tx:
            print(f"\n--- TX ID: {tx.id} | Account: {tx.account_name} ---")
            p = tx.raw_json
            if p:
                for i, line in enumerate(p.get("Line", [])):
                    print(f"\nLine {i}:")
                    print(json.dumps(line, indent=2))
            else:
                print("❌ No raw_json available.")
        else:
            print("❌ Transaction 115 not found.")

    finally:
        db.close()

if __name__ == "__main__":
    diag_transactions_full()
