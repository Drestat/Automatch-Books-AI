
import modal
from app.services.qbo_client import QBOClient
from app.db.session import get_db
from app.models.qbo import QBOConnection
import json

app = modal.App.lookup("qbo-sync-engine", create_if_missing=False)

@app.function()
def inspect_specific_transactions():
    """Find specific transactions and print their full JSON"""
    print("🔍 Starting inspection...")
    db = next(get_db())
    
    try:
        # Get the first active connection
        connection = db.query(QBOConnection).first()
        if not connection:
            print("❌ No QBO connection found in database")
            return
            
        print(f"✅ Found connection for Realm ID: {connection.realm_id}")
        
        client = QBOClient(db, connection)
        
        # Query Purchases
        # We'll fetch a batch and search in Python to avoid complex API queries if possible, 
        # or just query generic "SELECT * FROM Purchase MAXRESULTS 100"
        query = "SELECT * FROM Purchase MAXRESULTS 100"
        result = client.query(query)
        
        purchases = result.get("QueryResponse", {}).get("Purchase", [])
        print(f"📊 Downloaded {len(purchases)} Purchase transactions")
        
        target_names = ["Books", "Squeaky"]
        found_count = 0
        
        for p in purchases:
            entity_name = p.get("EntityRef", {}).get("name", "")
            description = p.get("PrivateNote", "") # sometimes description is here
            
            # Also check Line items for description
            line_desc = ""
            if "Line" in p:
                for line in p["Line"]:
                    line_desc += line.get("Description", "") + " "
            
            full_text = f"{entity_name} {description} {line_desc}".lower()
            
            is_match = any(name.lower() in full_text for name in target_names)
            
            if is_match:
                found_count += 1
                print(f"\n🔎 FOUND MATCH: {entity_name}")
                print("="*60)
                print(f"ID: {p.get('Id')}")
                print(f"TotalAmt: {p.get('TotalAmt')}")
                print(f"LinkedTxn: {json.dumps(p.get('LinkedTxn'), indent=2)}")
                print(f"TxnType: {p.get('PaymentType')}")
                
                # Check for TxnType "54"
                purchase_ex = p.get("PurchaseEx", {})
                print(f"PurchaseEx: {json.dumps(purchase_ex, indent=2)}")
                
                print("-" * 20)
                print("FULL JSON:")
                print(json.dumps(p, indent=2))
                print("="*60)
                
        if found_count == 0:
            print("\n❌ Could not find 'Books By Bessie' or 'Squeaky Kleen' in the downloaded purchases.")
            print("First 3 transactions for reference:")
            for p in purchases[:3]:
                 print(f"- {p.get('EntityRef', {}).get('name', 'N/A')} : ${p.get('TotalAmt')}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_specific_transactions.remote()
