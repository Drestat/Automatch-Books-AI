
from app.db.session import SessionLocal
from app.models.qbo import Transaction
import sys

db = SessionLocal()

terms = ["Pam Seitz", "Books by Bessie"]
txs = []
for term in terms:
    txs.extend(db.query(Transaction).filter(Transaction.description.ilike(f"%{term}%")).all())

print(f"{'ID':<5} | {'Description':<20} | {'Reasoning':<20} | {'Tax Note':<20}")
print("-" * 80)

for tx in txs:
    r = tx.reasoning[:20] if tx.reasoning else "None"
    t = tx.tax_deduction_note[:20] if tx.tax_deduction_note else "None"
    print(f"{tx.id:<5} | {tx.description[:20]:<20} | {r:<20} | {t:<20}")
    
    # Also check specific sub-reasoning fields
    if tx.vendor_reasoning or tx.category_reasoning:
        print(f"   > Vendor Reas: {tx.vendor_reasoning}")
        print(f"   > Cat Reas: {tx.category_reasoning}")

db.close()
