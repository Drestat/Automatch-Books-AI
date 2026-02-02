import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def analyze_all_transaction_types():
    db = SessionLocal()
    try:
        # Get Checking account
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print(f"🔍 Analyzing ALL transaction types for Checking (ID: {checking.id})\n")
        print("="*80)
        
        # Define all transaction types to check
        queries = {
            "Purchase": "SELECT * FROM Purchase MAXRESULTS 1000",
            "Deposit": "SELECT * FROM Deposit MAXRESULTS 1000",
            "Transfer": "SELECT * FROM Transfer MAXRESULTS 1000",
            "JournalEntry": "SELECT * FROM JournalEntry MAXRESULTS 1000",
            "CreditCardCredit": "SELECT * FROM CreditCardCredit MAXRESULTS 1000",
        }
        
        all_transactions = []
        
        for entity_type, query in queries.items():
            try:
                result = client.query(query)
                entities = result.get("QueryResponse", {}).get(entity_type, [])
                
                # Filter for Checking account
                checking_txs = []
                for tx in entities:
                    # Different entity types use different fields for account reference
                    acc_id = None
                    
                    if entity_type == "Purchase":
                        acc_id = tx.get("AccountRef", {}).get("value")
                    elif entity_type == "Deposit":
                        acc_id = tx.get("DepositToAccountRef", {}).get("value")
                    elif entity_type == "Transfer":
                        from_acc = tx.get("FromAccountRef", {}).get("value")
                        to_acc = tx.get("ToAccountRef", {}).get("value")
                        if from_acc == checking.id or to_acc == checking.id:
                            acc_id = checking.id
                    elif entity_type == "JournalEntry":
                        # JournalEntry has multiple lines, check if any reference Checking
                        for line in tx.get("Line", []):
                            detail = line.get("JournalEntryLineDetail", {})
                            if detail.get("AccountRef", {}).get("value") == checking.id:
                                acc_id = checking.id
                                break
                    elif entity_type == "CreditCardCredit":
                        acc_id = tx.get("AccountRef", {}).get("value")
                    
                    if acc_id == checking.id:
                        # Check for LinkedTxn
                        linked_txns = tx.get("LinkedTxn", [])
                        has_linked = len(linked_txns) > 0
                        
                        checking_txs.append({
                            "id": tx.get("Id"),
                            "type": entity_type,
                            "date": tx.get("TxnDate"),
                            "amount": tx.get("TotalAmt") or tx.get("Amount", 0),
                            "has_linked": has_linked,
                            "linked_count": len(linked_txns)
                        })
                
                if checking_txs:
                    print(f"\n{entity_type}: {len(checking_txs)} transactions")
                    for tx in checking_txs[:3]:
                        status = "✅ CATEGORIZED" if tx["has_linked"] else "🟡 FOR REVIEW"
                        print(f"  {status} | ID: {tx['id']} | Date: {tx['date']} | ${tx['amount']}")
                    if len(checking_txs) > 3:
                        print(f"  ... and {len(checking_txs) - 3} more")
                    
                    all_transactions.extend(checking_txs)
                
            except Exception as e:
                print(f"⚠️  Error fetching {entity_type}: {e}")
        
        print("\n" + "="*80)
        print(f"\n📊 TOTAL SUMMARY:")
        print(f"Total Transactions: {len(all_transactions)}")
        
        categorized = [tx for tx in all_transactions if tx["has_linked"]]
        for_review = [tx for tx in all_transactions if not tx["has_linked"]]
        
        print(f"Categorized (has LinkedTxn): {len(categorized)}")
        print(f"For Review (no LinkedTxn): {len(for_review)}")
        
        print("\n" + "="*80)
        print("\n🟢 CATEGORIZED TRANSACTIONS:")
        for tx in categorized:
            print(f"  ID: {tx['id']} | Type: {tx['type']} | Date: {tx['date']} | ${tx['amount']}")
        
        if not categorized:
            print("  (None)")
        
    finally:
        db.close()

if __name__ == "__main__":
    analyze_all_transaction_types()
