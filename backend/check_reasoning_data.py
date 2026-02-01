from app.db.session import SessionLocal
from app.models.qbo import Transaction
import json

def check_data():
    db = SessionLocal()
    try:
        # Check ANY transaction with vendor_reasoning
        txs = db.query(Transaction).filter(Transaction.vendor_reasoning.isnot(None)).limit(5).all()

        print(f"Found {len(txs)} transactions with Vendor Reasoning.")
        for tx in txs:
            print(f"ID: {tx.id}")
            print(f"Desc: {tx.description}")
            print(f"Vendor Reasoning: {tx.vendor_reasoning}")
            print(f"Tax Note: {tx.tax_deduction_note}")
            print("-" * 20)

        # Check transactions appearing as Suggestion but missing Reasoning
        # Use filter for where suggested_category_id IS NOT NULL but reasoning IS NULL
        txs_empty = db.query(Transaction).filter(
            Transaction.suggested_category_id.isnot(None), 
            Transaction.vendor_reasoning == None
        ).limit(5).all()
        
        print(f"\nFound {len(txs_empty)} analyzed transactions WITHOUT reasoning.")
        for tx in txs_empty:
            print(f"ID: {tx.id} | Desc: {tx.description} | Status: {tx.status}")
            print(f"  Suggested: {tx.suggested_category_name}")
            print(f"  Reasoning (old field): {tx.reasoning}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
