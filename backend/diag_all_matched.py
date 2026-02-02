import os
import sys
import json
from sqlalchemy.orm import Session

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diag_matched_txs():
    db = SessionLocal()
    try:
        txs = db.query(Transaction).all()
        print(f"Total Transactions: {len(txs)}")
        
        matched = [tx for tx in txs if tx.is_qbo_matched]
        unmatched = [tx for tx in txs if not tx.is_qbo_matched]
        
        print(f"Matched: {len(matched)}")
        print(f"Unmatched: {len(unmatched)}")
        
        print("\n--- Samples of Matched Transactions ---")
        for tx in matched[:10]:
            print(f"\nID: {tx.id} | Desc: {tx.description} | Amount: {tx.amount}")
            print(f"Reasoning: {tx.reasoning}")
            
            # Check Line structure
            raw = tx.raw_json or {}
            lines = raw.get("Line", [])
            for i, line in enumerate(lines):
                linked = line.get("LinkedTxn", [])
                print(f"  Line {i}: LinkedTxn Count: {len(linked)}")
                # Check for AccountRef
                for detail_key in ["AccountBasedExpenseLineDetail", "JournalEntryLineDetail", "DepositLineDetail", "SalesItemLineDetail", "ItemBasedExpenseLineDetail"]:
                    if detail_key in line:
                        detail = line[detail_key]
                        acc_ref = detail.get("AccountRef", {})
                        item_ref = detail.get("ItemRef", {})
                        if acc_ref:
                            print(f"    {detail_key}.AccountRef: {acc_ref.get('name')} ({acc_ref.get('value')})")
                        if item_ref:
                            print(f"    {detail_key}.ItemRef: {item_ref.get('name')} ({item_ref.get('value')})")

    finally:
        db.close()

if __name__ == "__main__":
    diag_matched_txs()
