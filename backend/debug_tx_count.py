from app.db.session import SessionLocal
from app.models.qbo import Transaction
import json

db = SessionLocal()
count = db.query(Transaction).count()
print(f"Total Transactions: {count}")

# Check first 5
txs = db.query(Transaction).limit(5).all()
for tx in txs:
    print(f"ID: {tx.id}, Desc: {tx.description}, Realm: {tx.realm_id}")

db.close()
