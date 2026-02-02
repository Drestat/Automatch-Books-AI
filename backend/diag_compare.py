import sys
import os
import json
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def compare_items():
    db = SessionLocal()
    try:
        # ID 138 is CONFIRMED "Categorized"
        # ID 136 is PRESUMED "For Review" (Same payee/amount, different date)
        
        tx_138 = db.query(Transaction).filter(Transaction.id == '138').first()
        tx_136 = db.query(Transaction).filter(Transaction.id == '136').first()
        
        print("\n=== ID 138 (CATEGORIZED) ===")
        print(json.dumps(tx_138.raw_json, indent=2))
        
        print("\n=== ID 136 (FOR REVIEW) ===")
        print(json.dumps(tx_136.raw_json, indent=2))

    finally:
        db.close()

if __name__ == "__main__":
    compare_items()
