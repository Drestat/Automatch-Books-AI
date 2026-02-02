import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def check_txntype_54():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Checking ONLY TxnType 54 transactions...\n")
        
        # Fetch Purchases
        result = client.query("SELECT * FROM Purchase MAXRESULTS 1000")
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        checking_purchases = [
            tx for tx in all_purchases 
            if tx.get("AccountRef", {}).get("value") == checking.id
        ]
        
        txntype_54_count = 0
        
        print("="*80)
        print("🎯 TRANSACTIONS WITH TXNTYPE 54:")
        print("="*80)
        
        for tx in checking_purchases:
            # Skip voided/deleted
            if tx.get("TxnStatus") in ["Voided", "Deleted"]:
                continue
            
            # Check TxnType
            purchase_ex = tx.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
                        if txn_type == "54":
                            txntype_54_count += 1
                            
                            # Get category
                            category = "N/A"
                            for line in tx.get("Line", []):
                                if "AccountBasedExpenseLineDetail" in line:
                                    category = line["AccountBasedExpenseLineDetail"].get("AccountRef", {}).get("name", "N/A")
                            
                            print(f"\nID: {tx.get('Id')}")
                            print(f"  Date: {tx.get('TxnDate')}")
                            print(f"  Entity: {tx.get('EntityRef', {}).get('name')}")
                            print(f"  Amount: ${tx.get('TotalAmt')}")
                            print(f"  Category: {category}")
                            print(f"  Created: {tx.get('MetaData', {}).get('CreateTime')}")
                            print(f"  Updated: {tx.get('MetaData', {}).get('LastUpdatedTime')}")
                            break
        
        print("\n" + "="*80)
        print(f"📊 TOTAL WITH TXNTYPE 54: {txntype_54_count}")
        print("="*80)
        
        # Also check Deposits
        print("\n\n🔍 Checking Deposits...\n")
        result = client.query("SELECT * FROM Deposit MAXRESULTS 1000")
        all_deposits = result.get("QueryResponse", {}).get("Deposit", [])
        
        checking_deposits = [
            tx for tx in all_deposits 
            if tx.get("DepositToAccountRef", {}).get("value") == checking.id
        ]
        
        print(f"Total Deposits to Checking: {len(checking_deposits)}")
        for tx in checking_deposits:
            if tx.get("TxnStatus") not in ["Voided", "Deleted"]:
                print(f"\nDeposit ID: {tx.get('Id')}")
                print(f"  Date: {tx.get('TxnDate')}")
                print(f"  Amount: ${tx.get('TotalAmt')}")
                print(f"  LinkedTxn: {tx.get('LinkedTxn', [])}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_txntype_54()
