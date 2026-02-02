import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def find_categorized_transaction():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Searching for the CATEGORIZED transaction...\n")
        
        # Fetch all Purchases
        result = client.query("SELECT * FROM Purchase MAXRESULTS 1000")
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        checking_purchases = [
            tx for tx in all_purchases 
            if tx.get("AccountRef", {}).get("value") == checking.id
        ]
        
        print(f"Checking {len(checking_purchases)} Purchase transactions...\n")
        
        # Look for ANY transaction with LinkedTxn or other categorization indicators
        for tx in checking_purchases:
            tx_id = tx.get("Id")
            
            # Check multiple indicators
            has_linked = len(tx.get("LinkedTxn", [])) > 0
            
            # Check if Line has a non-Uncategorized category
            has_real_category = False
            category_name = None
            
            for line in tx.get("Line", []):
                if "AccountBasedExpenseLineDetail" in line:
                    detail = line["AccountBasedExpenseLineDetail"]
                    if "AccountRef" in detail:
                        cat_name = detail["AccountRef"].get("name", "")
                        if cat_name and "Uncategorized" not in cat_name:
                            has_real_category = True
                            category_name = cat_name
            
            # Check for PaymentMethodRef (sometimes indicates categorization)
            has_payment_method = "PaymentMethodRef" in tx
            
            # Check for Credit (might indicate it's matched to a bill/invoice)
            has_credit = "Credit" in tx
            
            # Print if it has ANY special indicator
            if has_linked or has_payment_method or has_credit:
                print(f"🔍 Transaction ID: {tx_id}")
                print(f"  LinkedTxn: {tx.get('LinkedTxn', [])}")
                print(f"  PaymentMethodRef: {tx.get('PaymentMethodRef', 'N/A')}")
                print(f"  Credit: {tx.get('Credit', 'N/A')}")
                print(f"  Category: {category_name}")
                print(f"  Full JSON:")
                print(json.dumps(tx, indent=2))
                print("\n" + "="*80 + "\n")
        
        # Also check Deposits
        print("\n🔍 Checking Deposit transactions...\n")
        result = client.query("SELECT * FROM Deposit MAXRESULTS 1000")
        all_deposits = result.get("QueryResponse", {}).get("Deposit", [])
        
        checking_deposits = [
            tx for tx in all_deposits 
            if tx.get("DepositToAccountRef", {}).get("value") == checking.id
        ]
        
        for tx in checking_deposits:
            tx_id = tx.get("Id")
            has_linked = len(tx.get("LinkedTxn", [])) > 0
            
            if has_linked:
                print(f"🎯 FOUND CATEGORIZED DEPOSIT: ID {tx_id}")
                print(json.dumps(tx, indent=2))
                print("\n" + "="*80 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    find_categorized_transaction()
