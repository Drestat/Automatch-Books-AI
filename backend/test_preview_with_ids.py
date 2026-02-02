import os
import sys
import json

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def test_preview_with_ids():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    # Get all accounts to simulate what the frontend would send
    accounts = db.query(BankAccount).filter(BankAccount.realm_id == connection.realm_id).all()
    selected_ids = [str(acc.id) for acc in accounts]
    
    print(f"Testing preview with selected IDs: {selected_ids}\n")
    
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
            print(f"  Fetched {len(txs)} {entity} transactions")
        except Exception as e:
            print(f"  Error fetching {q.split()[3]}: {e}")
    
    print(f"\nTotal transactions fetched: {len(all_txs)}")
    
    # Filter and count
    total = 0
    already_matched = 0
    to_analyze = 0
    
    for p in all_txs:
        acc_id = None
        if "AccountRef" in p:
            acc_id = str(p["AccountRef"].get("value"))
        elif "DepositToAccountRef" in p:
            acc_id = str(p["DepositToAccountRef"].get("value"))
        elif "FromAccountRef" in p:
            acc_id = str(p["FromAccountRef"].get("value"))
        
        matched_primary = acc_id and acc_id in selected_ids
        matched_secondary = False
        
        if not matched_primary and "ToAccountRef" in p:
            to_acc_id = str(p["ToAccountRef"].get("value"))
            matched_secondary = to_acc_id and to_acc_id in selected_ids
        
        if matched_primary or matched_secondary:
            total += 1
            # Check if has category
            has_category = False
            if "Line" in p:
                for line in p["Line"]:
                    if "AccountBasedExpenseLineDetail" in line:
                        detail = line["AccountBasedExpenseLineDetail"]
                        if "AccountRef" in detail:
                            cat_name = detail["AccountRef"].get("name", "")
                            if "Uncategorized" not in cat_name:
                                has_category = True
                                break
            
            if has_category:
                already_matched += 1
            else:
                to_analyze += 1
    
    result = {
        "total_transactions": total,
        "already_matched": already_matched,
        "to_analyze": to_analyze
    }
    
    print("\n" + "="*50)
    print("PREVIEW RESULT:")
    print(json.dumps(result, indent=2))
    print("="*50)

if __name__ == "__main__":
    test_preview_with_ids()
