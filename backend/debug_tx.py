from app.db.session import SessionLocal
from app.models.qbo import Transaction

def find_cake():
    db = SessionLocal()
    try:
        # Search in description or receipts
        txs = db.query(Transaction).filter(Transaction.description.ilike('%cake%')).all()
        print(f"🔍 Found {len(txs)} 'cake' transactions")
        for tx in txs:
            print(f"ID: {tx.id} | Type: {tx.transaction_type} | Desc: {tx.description} | Date: {tx.date} | Receipt: {tx.receipt_url}")
            
        # Also list some recent approvals
        print("\n⏳ Recent Approvals (last 5):")
        recent = db.query(Transaction).filter(Transaction.is_exported == True).order_by(Transaction.updated_at.desc()).limit(5).all()
        for tx in recent:
            print(f"ID: {tx.id} | Type: {tx.transaction_type} | Desc: {tx.description} | Exported: {tx.is_exported} | SyncToken: {tx.sync_token}")

    finally:
        db.close()

if __name__ == "__main__":
    find_cake()
