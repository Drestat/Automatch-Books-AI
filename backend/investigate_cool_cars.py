from app.db.session import SessionLocal
from app.models.qbo import Transaction

def investigate_cool_cars():
    db = SessionLocal()
    # Search by description or payee
    txs = db.query(Transaction).filter(
        (Transaction.description.ilike("%Cool Cars%")) | 
        (Transaction.payee.ilike("%Cool Cars%"))
    ).all()

    print(f"Found {len(txs)} transactions matching 'Cool Cars'")
    for tx in txs:
        print(f"--- Transaction {tx.id} ---")
        print(f"Date: {tx.date}")
        print(f"Amount: {tx.amount}")
        print(f"Description: {tx.description}")
        print(f"Type: {tx.transaction_type}")
        print(f"Status: {tx.status}")
        print(f"Category (App): {tx.category_name}")
        print(f"Memo: {tx.note}")
        print(f"Raw JSON Type: {tx.raw_json.get('PaymentType') if tx.raw_json else 'N/A'}")
        if tx.raw_json and 'Line' in tx.raw_json:
            lines = tx.raw_json['Line']
            print(f"Lines: {len(lines)}")
            if len(lines) > 0:
                print(f"Line Detail: {lines[0].get('DetailType')}")
                if 'LinkedTxn' in lines[0]:
                    print(f"Linked Transaction: {lines[0]['LinkedTxn']}")

if __name__ == "__main__":
    investigate_cool_cars()
