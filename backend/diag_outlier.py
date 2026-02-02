import sys
import os
import json
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diagnose_outlier():
    db = SessionLocal()
    try:
        # Filter for Checking Account (ID 35) and "Matched" logic
        txs = db.query(Transaction).filter(Transaction.account_id == '35').all()
        
        print(f"Analyzing {len(txs)} transactions for outlier...")
        
        matched_txs = []
        for tx in txs:
            desc_upper = (tx.description or "").upper()
            is_weak = "UNCATEGORIZED" in desc_upper or "OPENING BALANCE" in desc_upper
            
            # Reconstruct "Matched" logic: Not weak.
            if not is_weak:
                matched_txs.append(tx)
        
        print(f"Found {len(matched_txs)} potential 'Matched' candidates (User says only 1 is real).")
        
        for tx in matched_txs:
            raw = tx.raw_json
            # Extract key fields that might indicate "Accepted" status
            meta = raw.get("MetaData", {})
            status = raw.get("PaymentStatus") or raw.get("DepositToAccountRef", {}).get("name")
            # Check for linked txn which implies a Match in the register
            linked = "NO"
            if "Line" in raw:
                for line in raw["Line"]:
                    if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                        linked = "YES"
            
            print(f"ID: {tx.id} | Desc: {tx.description} | Date: {tx.date.date()} | Amt: {tx.amount}")
            print(f"  -> LinkedTxn: {linked}")
            print(f"  -> Created: {meta.get('CreateTime')}")
            print(f"  -> LastUpdated: {meta.get('LastUpdatedTime')}")
            # Any other fields?
            print(f"  -> SyncToken: {raw.get('SyncToken')}")
            print(f"  -> Domain: {raw.get('domain')}")
            print("-" * 40)
            
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_outlier()
