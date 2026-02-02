import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def find_squeaky_kleen():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Searching for Squeaky Kleen Car Wash transaction on 12/30/2025...\n")
        
        # Fetch all Purchases
        result = client.query("SELECT * FROM Purchase MAXRESULTS 1000")
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        # Find the specific transaction
        for tx in all_purchases:
            if (tx.get("AccountRef", {}).get("value") == checking.id and
                tx.get("TxnDate") == "2025-12-30" and
                "Squeaky Kleen" in tx.get("EntityRef", {}).get("name", "")):
                
                print(f"🎯 FOUND IT!")
                print(f"\nTransaction ID: {tx.get('Id')}")
                print(f"Date: {tx.get('TxnDate')}")
                print(f"Amount: ${tx.get('TotalAmt')}")
                print(f"Entity: {tx.get('EntityRef', {}).get('name')}")
                print(f"\nFull JSON:")
                print(json.dumps(tx, indent=2))
                print("\n" + "="*80)
                
                # Check specific fields
                print(f"\n🔍 KEY FIELDS:")
                print(f"LinkedTxn: {tx.get('LinkedTxn', [])}")
                print(f"TxnStatus: {tx.get('TxnStatus')}")
                print(f"ReconcileStatus: {tx.get('ReconcileStatus')}")
                print(f"Credit: {tx.get('Credit')}")
                
                # Check Line items
                print(f"\n📋 LINE ITEMS:")
                for i, line in enumerate(tx.get("Line", [])):
                    print(f"\nLine {i+1}:")
                    print(json.dumps(line, indent=2))
                
                break
        
    finally:
        db.close()

if __name__ == "__main__":
    find_squeaky_kleen()
