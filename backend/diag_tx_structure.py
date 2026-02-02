import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diag_transactions():
    db = SessionLocal()
    try:
        # Get transactions that are NOT matched but have raw_json
        txs = db.query(Transaction).filter(
            Transaction.is_qbo_matched == False
        ).limit(5).all()
        
        print(f"🔍 Investigating {len(txs)} unmatched transactions...")
        
        for tx in txs:
            print(f"\n--- TX ID: {tx.id} | Account: {tx.account_name} ({tx.account_id}) ---")
            print(f"Description: {tx.description}")
            print(f"Amount: {tx.amount}")
            
            p = tx.raw_json
            if not p:
                print("❌ No raw_json available.")
                continue
                
            print(f"Entity Type: {p.get('Id')}") # This is just the ID, doesn't tell us type easily
            
            # Show Line structure
            lines = p.get("Line", [])
            print(f"Lines found: {len(lines)}")
            for i, line in enumerate(lines):
                print(f"  Line {i}: Keys: {list(line.keys())}")
                for detail_key in ["AccountBasedExpenseLineDetail", "JournalEntryLineDetail", "DepositLineDetail", "SalesItemLineDetail"]:
                    if detail_key in line:
                        detail = line[detail_key]
                        acc_ref = detail.get("AccountRef", {})
                        print(f"    - {detail_key} -> AccountRef: {acc_ref.get('name')} ({acc_ref.get('value')})")
            
            # Also check if it's a Transfer
            if "FromAccountRef" in p or "ToAccountRef" in p:
                print(f"  Header Refs: From: {p.get('FromAccountRef', {}).get('name')}, To: {p.get('ToAccountRef', {}).get('name')}")

    finally:
        db.close()

if __name__ == "__main__":
    diag_transactions()
