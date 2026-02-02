import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction

def diagnose_checking():
    db = SessionLocal()
    try:
        # Filter for Checking Account (ID 35)
        txs = db.query(Transaction).filter(Transaction.account_id == '35').all()
        
        print(f"Total Transactions in Checking (ID 35): {len(txs)}")
        
        to_review_count = 0
        matched_count = 0
        excluded_count = 0
        
        print("\n--- DETAIL ---")
        for tx in txs:
            # Replicate Frontend Logic
            # To Review: !excluded AND (pending OR (!matched AND !approved) OR forced)
            # Matched: !excluded AND matched AND !forced AND !approved
            # Excluded: excluded
            
            status = "UNKNOWN"
            if tx.is_excluded:
                status = "EXCLUDED"
                excluded_count += 1
            elif tx.forced_review:
                status = "FORCED_REVIEW"
                to_review_count += 1
            elif tx.is_qbo_matched and tx.status != 'approved':
                status = "MATCHED"
                matched_count += 1
            elif tx.status == 'approved':
                status = "APPROVED_DONE"
                # User probably doesn't count these in "For Review" or "Categorized" tabs if they are "Done" in our app?
                # But QBO "Categorized" tab usually means "Done".
                matched_count += 1 
            else:
                status = "TO_REVIEW"
                to_review_count += 1
            
            desc_upper = (tx.description or "").upper()
            is_weak = "UNCATEGORIZED" in desc_upper or "OPENING BALANCE" in desc_upper
            
            print(f"[{status}] {tx.date.date()} | {tx.amount} | {tx.description} (WeakDesc: {is_weak}) | QBO_Matched: {tx.is_qbo_matched}")

        print("\n--- SUMMARY ---")
        print(f"To Review: {to_review_count}")
        print(f"Matched (Inc. Approved): {matched_count}")
        print(f"Excluded: {excluded_count}")
        
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_checking()
