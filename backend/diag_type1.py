import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import Transaction
from app.core.feed_logic import FeedLogic

def diag_type1():
    db = SessionLocal()
    try:
        # Search for any transaction with TxnType="1" in raw_json
        # Since raw_json is JSONB, we can't easily query inside it with simple SQL using sqlalchemy core filtering without specific dialect support.
        # We'll just fetch recent 100 transactions and filter in python.
        
        txs = db.query(Transaction).limit(200).all()
        
        count = 0
        print("Searching for TxnType='1' (Bank Feed Import)...")
        
        for tx in txs:
            if not tx.raw_json: continue
            
            # Extract TxnType
            txn_type = "1" # Default
            purchase_ex = tx.raw_json.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
                        break
            
            if txn_type == "1":
                count += 1
                is_matched, reason = FeedLogic.analyze(tx.raw_json)
                
                print(f"\n" + "="*50)
                print(f"TX ID: {tx.id} | Date: {tx.date}")
                print(f"Description: {tx.description}")
                print(f"SyncToken: {tx.raw_json.get('SyncToken')}")
                print(f"ClrStatus: {FeedLogic._get_clr_status(tx.raw_json)}")
                print(f"HasCategory: {FeedLogic._has_specific_category(tx.raw_json)}")
                print(f"HasPayee: {FeedLogic._has_payee(tx.raw_json)}")
                print(f"Logic Decision: {is_matched} ({reason})")
                print("="*50)
                
                if count >= 10: break

        if count == 0:
            print("No TxnType='1' transactions found in the sample.")

    finally:
        db.close()

if __name__ == "__main__":
    diag_type1()
