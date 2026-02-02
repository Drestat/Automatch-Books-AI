import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def find_the_one_categorized():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Searching for the 1 CATEGORIZED transaction in QBO...\n")
        
        # Fetch ALL transaction types
        queries = {
            "Purchase": "SELECT * FROM Purchase MAXRESULTS 1000",
            "Deposit": "SELECT * FROM Deposit MAXRESULTS 1000",
            "Transfer": "SELECT * FROM Transfer MAXRESULTS 1000",
            "JournalEntry": "SELECT * FROM JournalEntry MAXRESULTS 1000",
        }
        
        all_checking_txs = []
        categorized_txs = []
        voided_txs = []
        
        for entity_type, query in queries.items():
            try:
                result = client.query(query)
                entities = result.get("QueryResponse", {}).get(entity_type, [])
                
                for tx in entities:
                    # Check if it belongs to Checking
                    belongs_to_checking = False
                    
                    if entity_type == "Purchase":
                        if tx.get("AccountRef", {}).get("value") == checking.id:
                            belongs_to_checking = True
                    elif entity_type == "Deposit":
                        if tx.get("DepositToAccountRef", {}).get("value") == checking.id:
                            belongs_to_checking = True
                    elif entity_type == "Transfer":
                        from_acc = tx.get("FromAccountRef", {}).get("value")
                        to_acc = tx.get("ToAccountRef", {}).get("value")
                        if from_acc == checking.id or to_acc == checking.id:
                            belongs_to_checking = True
                    elif entity_type == "JournalEntry":
                        for line in tx.get("Line", []):
                            detail = line.get("JournalEntryLineDetail", {})
                            if detail.get("AccountRef", {}).get("value") == checking.id:
                                belongs_to_checking = True
                                break
                    
                    if not belongs_to_checking:
                        continue
                    
                    # Check status
                    status = tx.get("TxnStatus", "")
                    if status in ["Voided", "Deleted"]:
                        voided_txs.append({
                            "id": tx.get("Id"),
                            "type": entity_type,
                            "status": status,
                            "amount": tx.get("TotalAmt") or tx.get("Amount", 0),
                            "date": tx.get("TxnDate")
                        })
                        continue  # Skip voided/deleted
                    
                    # Check for LinkedTxn
                    linked_txns = tx.get("LinkedTxn", [])
                    has_linked = len(linked_txns) > 0
                    
                    tx_info = {
                        "id": tx.get("Id"),
                        "type": entity_type,
                        "date": tx.get("TxnDate"),
                        "amount": tx.get("TotalAmt") or tx.get("Amount", 0),
                        "has_linked": has_linked,
                        "linked_txns": linked_txns,
                        "status": status
                    }
                    
                    all_checking_txs.append(tx_info)
                    
                    if has_linked:
                        categorized_txs.append(tx_info)
                        print(f"🎯 FOUND CATEGORIZED TRANSACTION!")
                        print(f"   ID: {tx_info['id']}")
                        print(f"   Type: {tx_info['type']}")
                        print(f"   Date: {tx_info['date']}")
                        print(f"   Amount: ${tx_info['amount']}")
                        print(f"   LinkedTxn: {json.dumps(linked_txns, indent=2)}")
                        print(f"   Full JSON:")
                        print(json.dumps(tx, indent=2))
                        print("\n" + "="*80 + "\n")
                
            except Exception as e:
                print(f"⚠️  Error fetching {entity_type}: {e}")
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Checking Transactions (excluding voided): {len(all_checking_txs)}")
        print(f"Categorized (has LinkedTxn): {len(categorized_txs)}")
        print(f"For Review (no LinkedTxn): {len(all_checking_txs) - len(categorized_txs)}")
        print(f"Voided/Deleted: {len(voided_txs)}")
        
        if voided_txs:
            print(f"\n🗑️  VOIDED/DELETED TRANSACTIONS:")
            for tx in voided_txs:
                print(f"   ID: {tx['id']} | Type: {tx['type']} | Status: {tx['status']} | ${tx['amount']}")
        
        if not categorized_txs:
            print(f"\n⚠️  NO CATEGORIZED TRANSACTIONS FOUND!")
            print(f"This means QBO UI might be showing cached data or using different logic.")
        
    finally:
        db.close()

if __name__ == "__main__":
    find_the_one_categorized()
