import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diag_missing():
    db = SessionLocal()
    try:
        print("Searching for specific missing transactions...")
        
        # 1. Search for $228.75 (01/01/2026)
        print("\n--- Specimen 1: $228.75 ---")
        txs1 = db.query(Transaction).filter(
            Transaction.amount == 228.75
        ).all()
        
        if not txs1:
            print("❌ No transaction found with amount 228.75")
        else:
            for tx in txs1:
                print(f"✅ Found ID: {tx.id} | Date: {tx.date} | Desc: {tx.description}")
                print(f"   Status: {tx.status} | QBO Matched: {tx.is_qbo_matched} | Excluded: {tx.is_excluded}")
                print(f"   Raw TxnType: {tx.raw_json.get('TxnType', 'N/A')}")

        # 2. Search for ALL Hicks
        print("\n--- All Hicks Hardware ---")
        txs2 = db.query(Transaction).filter(
            Transaction.description.ilike("%Hicks%")
        ).all()
        
        if not txs2:
            print("❌ No Hicks found")
        else:
            for tx in txs2:
                print(f"✅ Found ID: {tx.id} | Date: {tx.date} | Amount: {tx.amount} | Desc: {tx.description}")
                print(f"   Status: {tx.status} | QBO Matched: {tx.is_qbo_matched}")

    finally:
        db.close()

if __name__ == "__main__":
    diag_missing()
