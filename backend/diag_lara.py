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

def diag_lara():
    db = SessionLocal()
    try:
        # Search for "Lara's Lamination"
        print("Searching for 'Lara's Lamination'...")
        # Try exact match or ilike
        txs = db.query(Transaction).filter(
            Transaction.description.ilike("%Lara's Lamination%")
        ).all()
        
        if not txs:
            print("No transactions found matching 'Lara's Lamination'")
            return

        for tx in txs:
            print(f"\n" + "="*50)
            print(f"TX ID: {tx.id}")
            print(f"Description: {tx.description}")
            print(f"Current DB is_qbo_matched: {tx.is_qbo_matched}")
            
            # TEST NEW LOGIC
            is_matched, reason = FeedLogic.analyze(tx.raw_json)
            print(f"NEW LOGIC RESULT -> is_matched: {is_matched}")
            print(f"Reason: {reason}")
            
            print("-" * 20)
            # print("RAW JSON:")
            # print(json.dumps(tx.raw_json, indent=2))
            print("="*50)
            
            # OPTIONAL: Update DB to reflect new logic if correct
            if is_matched and not tx.is_qbo_matched:
                print("UPDATING DB RECORD...")
                tx.is_qbo_matched = True
                tx.status = 'approved' # Since it's matched/categorized
                tx.suggested_category_name = "Job Expenses:Job Materials" # From raw data
                db.add(tx)
                db.commit()
                print("DB Updated.")

    finally:
        db.close()

if __name__ == "__main__":
    diag_lara()
