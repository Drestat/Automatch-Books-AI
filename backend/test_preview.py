import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def test_preview():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    # Get active accounts
    active_banks = db.query(BankAccount).filter(
        BankAccount.realm_id == connection.realm_id,
        BankAccount.is_active == True
    ).all()
    
    selected_ids = [b.id for b in active_banks]
    print(f"Selected account IDs: {selected_ids}\n")
    
    # Simulate the preview endpoint logic
    qbo = QBOClient(db, connection)
    
    queries = [
        "SELECT * FROM Purchase MAXRESULTS 1000",
        "SELECT * FROM Deposit MAXRESULTS 500",
        "SELECT * FROM CreditCardCredit MAXRESULTS 500",
        "SELECT * FROM JournalEntry MAXRESULTS 500",
        "SELECT * FROM Transfer MAXRESULTS 500"
    ]
    
    all_txs = []
    for q in queries:
        try:
            res = qbo.query(q)
            entity = q.split()[3]
            txs = res.get("QueryResponse", {}).get(entity, [])
            all_txs.extend(txs)
        except Exception as e:
            print(f"Error: {e}")
    
    # Filter and count
    total = 0
    already_matched = 0
    to_analyze = 0
    
    for p in all_txs:
        acc_id = None
        if "AccountRef" in p:
            acc_id = p["AccountRef"].get("value")
        elif "DepositToAccountRef" in p:
            acc_id = p["DepositToAccountRef"].get("value")
        elif "FromAccountRef" in p:
            acc_id = p["FromAccountRef"].get("value")
        
        if acc_id and acc_id in selected_ids:
            total += 1
            # Check if has category
            if p.get("AccountBasedExpenseLineDetail") or p.get("Line"):
                already_matched += 1
            else:
                to_analyze += 1
        elif "ToAccountRef" in p:
            to_acc_id = p["ToAccountRef"].get("value")
            if to_acc_id and to_acc_id in selected_ids:
                total += 1
                if p.get("AccountBasedExpenseLineDetail") or p.get("Line"):
                    already_matched += 1
                else:
                    to_analyze += 1
    
    result = {
        "total_transactions": total,
        "already_matched": already_matched,
        "to_analyze": to_analyze
    }
    
    print("Preview Result:")
    print(result)

if __name__ == "__main__":
    test_preview()
