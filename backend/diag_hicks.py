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

def diag_hicks():
    db = SessionLocal()
    try:
        # Search for "Hicks"
        print("Searching for 'Hicks Hardware'...")
        txs = db.query(Transaction).filter(
            Transaction.description.ilike("%Hicks Hardware%")
        ).all()
        
        if not txs:
            print("No transactions found matching 'Hicks Hardware'")
            return

        for tx in txs:
            print(f"\n" + "="*50)
            print(f"TX ID: {tx.id}")
            print(f"Description: {tx.description}")
            print(f"Current DB is_qbo_matched: {tx.is_qbo_matched}")
            
            # TEST LOGIC
            is_matched, reason = FeedLogic.analyze(tx.raw_json)
            print(f"LOGIC RESULT -> is_matched: {is_matched}")
            print(f"Reason: {reason}")
            
            print("-" * 20)
            print("RAW JSON:")
            print(json.dumps(tx.raw_json, indent=2))
            print("="*50)

            # OPTIONAL: Update DB to reflect new logic if correct
            # For Hicks, we expect is_matched to be False (downgrade to For Review)
            if not is_matched and tx.is_qbo_matched:
                print("DOWNGRADING DB RECORD (Categorized -> For Review)...")
                tx.is_qbo_matched = False
                tx.status = 'unmatched'
                # We typically keep the detailed category info as suggestions
                # so the UI can show "Suggested Category"
                db.add(tx)
                db.commit()
                print("DB Updated.")
            
            # For Manual entries, we expect upgrade
            if is_matched and not tx.is_qbo_matched:
                print("UPGRADING DB RECORD (For Review -> Categorized)...")
                tx.is_qbo_matched = True
                tx.status = 'approved'
                db.add(tx)
                db.commit()
                print("DB Updated.")

    finally:
        db.close()

if __name__ == "__main__":
    diag_hicks()
