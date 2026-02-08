from app.db.session import SessionLocal
from app.models.qbo import Transaction
import json

def query():
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == '133').first()
    if tx:
        print(f"ID: {tx.id}")
        print(f"Description: {tx.description}")
        print(f"Amount: {tx.amount}")
        print(f"Type: {tx.transaction_type}")
        print(f"Status: {tx.status}")
        print(f"Receipt URL: {tx.receipt_url}")
        print(f"Has Binary: {tx.receipt_content is not None}")
    else:
        print("Transaction 133 not found")
        # Search by description
        matches = db.query(Transaction).filter(Transaction.description.ilike('%Chin%')).all()
        for m in matches:
            print(f"FOUND: ID={m.id}, Desc={m.description}, Type={m.transaction_type}, Amount={m.amount}")

if __name__ == "__main__":
    query()
