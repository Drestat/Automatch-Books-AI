
from app.db.session import SessionLocal
from app.models.qbo import Transaction
from app.core.feed_logic import FeedLogic
import sys

db = SessionLocal()
terms = ["Pam Seitz", "Books by Bessie"]

print(f"{'Description':<30} | {'Old Matched':<11} | {'Old Reason':<30} | {'New Matched':<11} | {'New Reason'}")
print("-" * 150)

for term in terms:
    txs = db.query(Transaction).filter(Transaction.description.ilike(f"%{term}%")).all()
    for tx in txs:
        if not tx.raw_json:
            continue
            
        old_matched = tx.is_qbo_matched
        old_reason = tx.reasoning or "N/A" # Using reasoning field as proxy for logic reason, though actual Logic returns it separately.
        
        # Run Logic
        is_matched, reason = FeedLogic.analyze(tx.raw_json)
        
        print(f"{tx.description[:30]:<30} | {str(old_matched):<11} | {old_reason[:30]:<30} | {str(is_matched):<11} | {reason}")
        
        # Update DB
        tx.is_qbo_matched = is_matched
        # Store reason in a field? We don't have a specific `feed_logic_reason` field, but we can print it.
        # Maybe update reasoning? No, reasoning is for AI.
        # Just update status.
        db.add(tx)

db.commit()
db.close()
