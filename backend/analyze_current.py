import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def analyze_current_state():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Analyzing current QBO state for Checking account...\n")
        
        # Fetch all transaction types
        queries = {
            "Purchase": "SELECT * FROM Purchase MAXRESULTS 1000",
            "Deposit": "SELECT * FROM Deposit MAXRESULTS 1000",
        }
        
        all_checking_txs = []
        categorized_count = 0
        for_review_count = 0
        
        for entity_type, query in queries.items():
            try:
                result = client.query(query)
                entities = result.get("QueryResponse", {}).get(entity_type, [])
                
                for tx in entities:
                    # Check if belongs to Checking
                    belongs_to_checking = False
                    if entity_type == "Purchase":
                        if tx.get("AccountRef", {}).get("value") == checking.id:
                            belongs_to_checking = True
                    elif entity_type == "Deposit":
                        if tx.get("DepositToAccountRef", {}).get("value") == checking.id:
                            belongs_to_checking = True
                    
                    if not belongs_to_checking:
                        continue
                    
                    # Skip voided/deleted
                    if tx.get("TxnStatus") in ["Voided", "Deleted"]:
                        continue
                    
                    # Check categorization indicators
                    has_linked_txn = len(tx.get("LinkedTxn", [])) > 0
                    
                    # Check TxnType
                    is_manually_categorized = False
                    purchase_ex = tx.get("PurchaseEx", {})
                    if "any" in purchase_ex:
                        for item in purchase_ex["any"]:
                            if item.get("value", {}).get("Name") == "TxnType":
                                txn_type = item.get("value", {}).get("Value")
                                if txn_type == "54":
                                    is_manually_categorized = True
                                    break
                    
                    # Check for Line Description
                    has_line_description = False
                    if "Line" in tx:
                        for line in tx["Line"]:
                            if "Description" in line and line["Description"]:
                                has_line_description = True
                                break
                    
                    # Determine status
                    is_categorized = has_linked_txn or is_manually_categorized or has_line_description
                    
                    tx_info = {
                        "id": tx.get("Id"),
                        "type": entity_type,
                        "date": tx.get("TxnDate"),
                        "amount": tx.get("TotalAmt") or tx.get("Amount", 0),
                        "entity": tx.get("EntityRef", {}).get("name", "N/A"),
                        "has_linked_txn": has_linked_txn,
                        "is_manually_categorized": is_manually_categorized,
                        "has_line_description": has_line_description,
                        "is_categorized": is_categorized,
                        "txn_type": None
                    }
                    
                    # Get TxnType for display
                    if "any" in purchase_ex:
                        for item in purchase_ex["any"]:
                            if item.get("value", {}).get("Name") == "TxnType":
                                tx_info["txn_type"] = item.get("value", {}).get("Value")
                    
                    all_checking_txs.append(tx_info)
                    
                    if is_categorized:
                        categorized_count += 1
                    else:
                        for_review_count += 1
                
            except Exception as e:
                print(f"⚠️  Error fetching {entity_type}: {e}")
        
        print(f"📊 SUMMARY:")
        print(f"Total Transactions: {len(all_checking_txs)}")
        print(f"Categorized: {categorized_count}")
        print(f"For Review: {for_review_count}\n")
        
        print("="*80)
        print("🟢 CATEGORIZED TRANSACTIONS:")
        print("="*80)
        for tx in all_checking_txs:
            if tx["is_categorized"]:
                print(f"ID: {tx['id']} | {tx['entity']} | ${tx['amount']} | {tx['date']}")
                print(f"  TxnType: {tx['txn_type']}")
                print(f"  LinkedTxn: {tx['has_linked_txn']}")
                print(f"  Manual: {tx['is_manually_categorized']}")
                print(f"  Has Description: {tx['has_line_description']}")
                print()
        
        print("="*80)
        print(f"🟡 FOR REVIEW TRANSACTIONS (showing first 5 of {for_review_count}):")
        print("="*80)
        count = 0
        for tx in all_checking_txs:
            if not tx["is_categorized"] and count < 5:
                print(f"ID: {tx['id']} | {tx['entity']} | ${tx['amount']} | {tx['date']}")
                print(f"  TxnType: {tx['txn_type']}")
                print()
                count += 1
        
    finally:
        db.close()

if __name__ == "__main__":
    analyze_current_state()
