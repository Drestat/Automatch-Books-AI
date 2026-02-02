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
        
        print("\n--- Detailed Audit of Matched Transactions ---")
        for tx in matched:
            print(f"\nID: {tx.id} | Desc: {tx.description} | Source Acc: {tx.account_id}")
            print(f"Reasoning: {tx.reasoning}")
            
            raw = tx.raw_json or {}
            lines = raw.get("Line", [])
            for i, line in enumerate(lines):
                for detail_key in ["AccountBasedExpenseLineDetail", "JournalEntryLineDetail", "DepositLineDetail", "SalesItemLineDetail", "ItemBasedExpenseLineDetail"]:
                    if detail_key in line:
                        detail = line[detail_key]
                        acc_ref = detail.get("AccountRef", {})
                        if acc_ref:
                            ref_id = str(acc_ref.get('value'))
                            ref_name = acc_ref.get('name')
                            print(f"  Line {i}: {detail_key}.AccountRef: {ref_name} ({ref_id})")
                            if ref_id == str(tx.account_id):
                                print(f"    ⚠️  MATCHES SOURCE ACCOUNT! This should not be a category.")

    finally:
        db.close()

if __name__ == "__main__":
    diag_matched_txs()
