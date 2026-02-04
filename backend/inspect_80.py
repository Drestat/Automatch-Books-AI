import os
import sys
import json
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def inspect_tx_80():
    db = SessionLocal()
    try:
        print("Inspecting Transaction 80...")
        tx = db.query(Transaction).filter(Transaction.id == "80").first()
        if tx:
            print(f"ID: {tx.id}")
            print(f"Amount: {tx.amount}")
            print(f"Date: {tx.date}")
            print(f"Description: {tx.description}")
            print("Raw JSON:")
            print(json.dumps(tx.raw_json, indent=2))
        else:
            print("Transaction 80 not found.")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_tx_80()
