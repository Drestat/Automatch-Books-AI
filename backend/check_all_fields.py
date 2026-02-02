import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def check_all_transaction_fields():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Checking ALL fields for categorization indicators...\n")
        
        # Fetch Purchases
        result = client.query("SELECT * FROM Purchase MAXRESULTS 1000")
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        checking_purchases = [
            tx for tx in all_purchases 
            if tx.get("AccountRef", {}).get("value") == checking.id
        ]
        
        print(f"Analyzing {len(checking_purchases)} Purchase transactions\n")
        print("="*80)
        
        # Check for various indicators
        for tx in checking_purchases:
            tx_id = tx.get("Id")
            
            # Collect all possible categorization indicators
            indicators = {
                "LinkedTxn": tx.get("LinkedTxn", []),
                "ReconcileStatus": tx.get("ReconcileStatus"),
                "ClearedStatus": tx.get("ClearedStatus"),
                "TxnStatus": tx.get("TxnStatus"),
                "Credit": tx.get("Credit"),
                "PaymentType": tx.get("PaymentType"),
                "PaymentMethodRef": tx.get("PaymentMethodRef"),
                "EntityRef": tx.get("EntityRef"),
                "DocNumber": tx.get("DocNumber"),
            }
            
            # Check Line items for category
            has_category = False
            category_name = None
            for line in tx.get("Line", []):
                if "AccountBasedExpenseLineDetail" in line:
                    detail = line["AccountBasedExpenseLineDetail"]
                    if "AccountRef" in detail:
                        category_name = detail["AccountRef"].get("name")
                        if category_name and "Uncategorized" not in category_name:
                            has_category = True
            
            # Print if it has ANY interesting indicator
            if (indicators["ReconcileStatus"] or 
                indicators["ClearedStatus"] or 
                indicators["Credit"] or 
                len(indicators["LinkedTxn"]) > 0 or
                indicators["TxnStatus"] not in [None, ""]):
                
                print(f"\n📝 Transaction ID: {tx_id}")
                print(f"   Date: {tx.get('TxnDate')}")
                print(f"   Amount: ${tx.get('TotalAmt')}")
                print(f"   Entity: {tx.get('EntityRef', {}).get('name', 'N/A')}")
                print(f"   Category: {category_name or 'N/A'}")
                print(f"\n   Indicators:")
                for key, value in indicators.items():
                    if value:
                        print(f"      {key}: {value}")
                print("="*80)
        
        # Also check Deposits
        print("\n\n🔍 Checking Deposit transactions...\n")
        result = client.query("SELECT * FROM Deposit MAXRESULTS 1000")
        all_deposits = result.get("QueryResponse", {}).get("Deposit", [])
        
        checking_deposits = [
            tx for tx in all_deposits 
            if tx.get("DepositToAccountRef", {}).get("value") == checking.id
        ]
        
        print(f"Analyzing {len(checking_deposits)} Deposit transactions\n")
        
        for tx in checking_deposits:
            tx_id = tx.get("Id")
            
            indicators = {
                "LinkedTxn": tx.get("LinkedTxn", []),
                "ReconcileStatus": tx.get("ReconcileStatus"),
                "ClearedStatus": tx.get("ClearedStatus"),
                "TxnStatus": tx.get("TxnStatus"),
            }
            
            if any(indicators.values()):
                print(f"\n📝 Deposit ID: {tx_id}")
                print(f"   Date: {tx.get('TxnDate')}")
                print(f"   Amount: ${tx.get('TotalAmt')}")
                print(f"\n   Indicators:")
                for key, value in indicators.items():
                    if value:
                        print(f"      {key}: {value}")
                print("="*80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_all_transaction_fields()
