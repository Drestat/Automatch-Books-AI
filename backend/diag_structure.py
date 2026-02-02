import sys
import os
import json
from collections import Counter

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diagnose_structure_distribution():
    db = SessionLocal()
    try:
        # Filter for Checking Account (ID 35)
        txs = db.query(Transaction).filter(Transaction.account_id == '35').all()
        
        print(f"Analyzing {len(txs)} transactions structure...")
        
        detail_types = []
        payment_types = []
        
        for tx in txs:
            raw = tx.raw_json
            p_type = raw.get("PaymentType", "Unknown")
            payment_types.append(p_type)
            
            lines = raw.get("Line", [])
            for line in lines:
                d_type = line.get("DetailType", "Unknown")
                # We only care about the first line usually, or main lines
                if d_type != "Unknown":
                    detail_types.append(f"{tx.id}:{d_type}")
        
        print("\nPayment Types Distribution:")
        print(Counter(payment_types))
        
        print("\nDetail Types (first few):")
        # Print all to find outlier
        for dt in detail_types:
            print(dt)

    finally:
        db.close()

if __name__ == "__main__":
    diagnose_structure_distribution()
