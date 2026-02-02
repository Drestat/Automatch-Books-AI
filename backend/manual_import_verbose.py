import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount, Transaction
from app.services.qbo_client import QBOClient
from datetime import datetime

def manual_import():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    print(f"Realm: {connection.realm_id}")
    
    # Get active accounts
    active_banks = db.query(BankAccount).filter(
        BankAccount.realm_id == connection.realm_id,
        BankAccount.is_active == True
    ).all()
    
    active_account_ids = [b.id for b in active_banks]
    print(f"Active accounts: {active_account_ids}\n")
    
    # Fetch transactions
    qbo = QBOClient(db, connection)
    
    queries = [
        "SELECT * FROM Purchase",
        "SELECT * FROM Deposit"
    ]
    
    all_txs = []
    for q in queries:
        try:
            res = qbo.query(q)
            entity = q.split()[3]
            txs = res.get("QueryResponse", {}).get(entity, [])
            all_txs.extend(txs)
            print(f"Fetched {len(txs)} {entity} transactions")
        except Exception as e:
            print(f"Error fetching {entity}: {e}")
    
    print(f"\nProcessing {len(all_txs)} transactions...")
    
    saved_count = 0
    for p in all_txs:
        # Resolve account ID
        acc_id = None
        acc_name = "Unknown"
        if "AccountRef" in p:
            acc_id = p["AccountRef"].get("value")
            acc_name = p["AccountRef"].get("name", "Unknown")
        elif "DepositToAccountRef" in p:
            acc_id = p["DepositToAccountRef"].get("value")
            acc_name = p["DepositToAccountRef"].get("name", "Unknown")
        
        if not acc_id or acc_id not in active_account_ids:
            continue
        
        # Create or update transaction
        tx = db.query(Transaction).filter(Transaction.id == p["Id"]).first()
        if not tx:
            tx = Transaction(id=p["Id"], realm_id=connection.realm_id)
            print(f"  Creating new transaction: {p['Id']}")
        
        tx.date = datetime.strptime(p["TxnDate"], "%Y-%m-%d")
        tx.account_id = acc_id
        tx.account_name = acc_name
        tx.description = p.get("PrivateNote", "")[:255] if p.get("PrivateNote") else "Transaction"
        tx.amount = float(p.get("TotalAmt", 0))
        tx.status = "unmatched"
        tx.is_qbo_matched = False
        
        db.add(tx)
        saved_count += 1
    
    print(f"\nCommitting {saved_count} transactions...")
    db.commit()
    print("✅ Done!")
    
    # Verify
    count = db.query(Transaction).filter(Transaction.realm_id == connection.realm_id).count()
    print(f"\nTotal transactions in DB: {count}")

if __name__ == "__main__":
    manual_import()
