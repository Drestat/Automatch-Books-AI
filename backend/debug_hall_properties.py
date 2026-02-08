import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection

def check_hall_properties():
    db = SessionLocal()
    
    # Find transactions with Hall Properties in description or payee
    query = db.query(Transaction).filter(
        (Transaction.description.ilike("%Hall Properties%")) |
        (Transaction.payee.ilike("%Hall Properties%"))
    )
    
    txs = query.all()
    print(f"Found {len(txs)} transactions matching 'Hall Properties'\n")
    
    for tx in txs:
        print(f"ID: {tx.id}")
        print(f"Date: {tx.date}")
        print(f"Description: {tx.description}")
        print(f"Payee: {tx.payee}")
        print(f"Amount: {tx.amount}")
        print(f"Status: {tx.status}")
        print(f"Type: {tx.transaction_type}")
        print(f"Receipt URL: {tx.receipt_url}")
        print(f"Receipt Content (bytes): {len(tx.receipt_content) if tx.receipt_content else 'None'}")
        print(f"Metadata: {tx.raw_json.get('Id') if tx.raw_json else 'None'}")
        print(f"Is QBO Matched: {tx.is_qbo_matched}")
        print("-" * 30)

if __name__ == "__main__":
    check_hall_properties()
