
from app.db.session import SessionLocal
from app.models.qbo import Transaction
import sys

db = SessionLocal()

# Search terms
terms = ["Pam Seitz", "Books by Bessie"]

print(f"{'ID':<5} | {'Date':<10} | {'Description':<30} | {'Amount':<10} | {'Type':<5} | {'Clr':<5} | {'Matched':<7} | {'Review':<6}")
print("-" * 100)

for term in terms:
    txs = db.query(Transaction).filter(Transaction.description.ilike(f"%{term}%")).all()
    for tx in txs:
            import json
            print(f"--- Raw JSON for {tx.description} (ID: {tx.id}) ---")
            print(json.dumps(tx.raw_json, indent=2))
            print("-" * 50)

db.close()
