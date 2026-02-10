
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def inspect_tx_155():
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == "155").first()
        if tx:
            print(f"Transaction 155:")
            print(f"  - Description: {tx.description}")
            print(f"  - Payee (Column): '{tx.payee}'")
            print(f"  - Suggested Payee: '{tx.suggested_payee}'")
            print(f"  - Entity Ref (Raw): {tx.raw_json.get('EntityRef') if tx.raw_json else 'None'}")
        else:
            print("❌ Transaction 155 not found.")
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_tx_155()
