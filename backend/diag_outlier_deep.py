import sys
import os
import json
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diagnose_outlier_deep():
    db = SessionLocal()
    try:
        # Filter for Checking Account (ID 35)
        txs = db.query(Transaction).filter(Transaction.account_id == '35').all()
        
        print(f"Deep Analysis of {len(txs)} transactions...")
        
        for tx in txs:
            # Only interest in "Matched" for now
            desc_upper = (tx.description or "").upper()
            is_weak = "UNCATEGORIZED" in desc_upper or "OPENING BALANCE" in desc_upper
            if is_weak: continue

            raw = tx.raw_json
            # Look for specific keys
            payment_status = raw.get("PaymentStatus")
            status = raw.get("status") # Sometimes present
            
            # Check for keys related to bank feed
            bank_desc = raw.get("BankTransactions", []) # Unlikely in Purchase object
            
            print(f"ID: {tx.id} | Desc: {tx.description} | Amt: {tx.amount}")
            print(f"  KEYS: {list(raw.keys())}")
            if "status" in raw: print(f"  -> status: {raw['status']}")
            
            # Print full JSON for ONE item to check structure
            if tx.id == '115': # Hicks Hardware
                print(f"  -> JSON: {json.dumps(raw, indent=2)}")

    finally:
        db.close()

if __name__ == "__main__":
    diagnose_outlier_deep()
