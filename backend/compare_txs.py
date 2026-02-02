import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def compare_transactions():
    db = SessionLocal()
    try:
        checking = db.query(BankAccount).filter(BankAccount.id == "35").first()
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == checking.realm_id).first()
        client = QBOClient(db, conn)
        
        print("🔍 Comparing Squeaky Kleen (Categorized) with other transactions (For Review)...\n")
        
        # Fetch all Purchases
        result = client.query("SELECT * FROM Purchase MAXRESULTS 1000")
        all_purchases = result.get("QueryResponse", {}).get("Purchase", [])
        
        checking_purchases = [
            tx for tx in all_purchases 
            if tx.get("AccountRef", {}).get("value") == checking.id
        ]
        
        # Find Squeaky Kleen (ID 145)
        squeaky = None
        others = []
        
        for tx in checking_purchases:
            if tx.get("Id") == "145":
                squeaky = tx
            else:
                others.append(tx)
        
        if not squeaky:
            print("❌ Squeaky Kleen transaction not found!")
            return
        
        print("="*80)
        print("🎯 SQUEAKY KLEEN (ID 145) - CATEGORIZED")
        print("="*80)
        print(json.dumps(squeaky, indent=2))
        
        print("\n\n" + "="*80)
        print("🔍 COMPARISON WITH OTHER TRANSACTIONS (FOR REVIEW)")
        print("="*80)
        
        # Compare with another transaction
        other = others[0] if others else None
        if other:
            print(f"\nOther Transaction (ID {other.get('Id')}) - FOR REVIEW:")
            print(json.dumps(other, indent=2))
        
        # Find key differences
        print("\n\n" + "="*80)
        print("🔑 KEY DIFFERENCES:")
        print("="*80)
        
        squeaky_keys = set(squeaky.keys())
        other_keys = set(other.keys()) if other else set()
        
        unique_to_squeaky = squeaky_keys - other_keys
        unique_to_other = other_keys - squeaky_keys
        
        if unique_to_squeaky:
            print(f"\n✅ Fields ONLY in Squeaky Kleen:")
            for key in unique_to_squeaky:
                print(f"   {key}: {squeaky[key]}")
        
        if unique_to_other:
            print(f"\n❌ Fields ONLY in other transaction:")
            for key in unique_to_other:
                print(f"   {key}: {other[key]}")
        
        # Compare common fields with different values
        print(f"\n🔄 Fields with DIFFERENT values:")
        for key in squeaky_keys & other_keys:
            if squeaky[key] != other[key]:
                print(f"\n   {key}:")
                print(f"      Squeaky: {squeaky[key]}")
                print(f"      Other: {other[key]}")
        
    finally:
        db.close()

if __name__ == "__main__":
    compare_transactions()
