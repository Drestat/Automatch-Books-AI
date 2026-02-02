import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount, Transaction
from app.services.qbo_client import QBOClient

def debug_sync():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    print(f"Realm: {connection.realm_id}\n")
    
    # Get active accounts
    active_banks = db.query(BankAccount).filter(
        BankAccount.realm_id == connection.realm_id,
        BankAccount.is_active == True
    ).all()
    
    if not active_banks:
        print("⚠️ No active accounts selected.")
        return
    
    active_account_ids = [b.id for b in active_banks]
    print(f"Active account IDs: {active_account_ids}\n")
    
    # Fetch transactions
    qbo = QBOClient(db, connection)
    
    queries = [
        "SELECT * FROM Purchase",
        "SELECT * FROM Deposit",
        "SELECT * FROM Transfer"
    ]
    
    all_txs = []
    for q in queries:
        try:
            res = qbo.query(q)
            entity = q.split()[3]
            txs = res.get("QueryResponse", {}).get(entity, [])
            all_txs.extend(txs)
            print(f"{entity}: {len(txs)} found")
        except Exception as e:
            print(f"{entity}: Error - {e}")
    
    print(f"\nTotal transactions fetched: {len(all_txs)}\n")
    
    # Filter by account
    valid_count = 0
    for p in all_txs:
        acc_id = None
        if "AccountRef" in p:
            acc_id = p["AccountRef"].get("value")
        elif "DepositToAccountRef" in p:
            acc_id = p["DepositToAccountRef"].get("value")
        elif "FromAccountRef" in p:
            acc_id = p["FromAccountRef"].get("value")
        
        if acc_id and acc_id in active_account_ids:
            valid_count += 1
        elif "ToAccountRef" in p:
            to_acc_id = p["ToAccountRef"].get("value")
            if to_acc_id and to_acc_id in active_account_ids:
                valid_count += 1
    
    print(f"Transactions matching active accounts: {valid_count}")
    
    if valid_count == 0:
        print("\n❌ NO TRANSACTIONS MATCH ACTIVE ACCOUNTS!")
        print("This means the account IDs in QuickBooks don't match the IDs in the database.")
        print("\nAccount IDs are STRINGS in QBO but might be stored as INTEGERS in the database.")
        print("Let me check...")
        
        for acc in active_banks:
            print(f"  DB Account ID: '{acc.id}' (type: {type(acc.id)})")

if __name__ == "__main__":
    debug_sync()
