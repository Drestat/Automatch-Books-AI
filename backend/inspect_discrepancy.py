import modal
import os
from dotenv import dotenv_values
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-discrepancy")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_discrepancy():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    from datetime import datetime
    import json
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    print(f"\n{'='*140}")
    print(f"INVESTIGATING NORTON LUMBER & TANIA'S NURSERY")
    print(f"{'='*140}\n")
    
    # Norton Lumber
    norton = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Norton Lumber%"),
        Transaction.date == datetime(2026, 1, 1),
        Transaction.amount == 103.55
    ).first()
    
    if norton:
        print(f"🔍 NORTON LUMBER (01/01/2026 - $103.55)")
        print(f"   Status in App: {'Categorized' if norton.is_qbo_matched else 'For Review'}")
        print(f"   Category: {norton.suggested_category_name}")
        
        # Check signals
        doc_number = norton.raw_json.get("DocNumber")
        line = norton.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        
        # Check TxnType
        purchase_ex = norton.raw_json.get("PurchaseEx", {})
        txn_type = "Not Found"
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    break
        
        print(f"\n   Technical Signals:")
        print(f"   - DocNumber: {doc_number if doc_number else '(None)'}")
        print(f"   - LinkedTxn: {has_linked}")
        print(f"   - TxnType: {txn_type}")
        print(f"   - Entity Type: {norton.raw_json.get('domain', 'Unknown')}")
        
        # Check if it's a BillPayment
        if "VendorRef" in norton.raw_json and "CreditCardPayment" in norton.raw_json:
            print(f"   - Type: BillPayment (CC Payment)")
        
        print(f"\n   RAW JSON KEYS:")
        print(f"   {list(norton.raw_json.keys())}")
        
        print(f"\n   FULL RAW JSON:")
        print(json.dumps(norton.raw_json, indent=2))
    
    print(f"\n{'-'*140}\n")
    
    # Tania's Nursery
    tania = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Tania's Nursery%"),
        Transaction.date == datetime(2025, 12, 26),
        Transaction.amount == 82.45
    ).first()
    
    if tania:
        print(f"🔍 TANIA'S NURSERY (12/26/2025 - $82.45)")
        print(f"   Status in App: {'Categorized' if tania.is_qbo_matched else 'For Review'}")
        print(f"   Category: {tania.suggested_category_name}")
        
        # Check signals
        doc_number = tania.raw_json.get("DocNumber")
        line = tania.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        
        # Check TxnType
        purchase_ex = tania.raw_json.get("PurchaseEx", {})
        txn_type = "Not Found"
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    break
        
        print(f"\n   Technical Signals:")
        print(f"   - DocNumber: {doc_number if doc_number else '(None)'}")
        print(f"   - LinkedTxn: {has_linked}")
        print(f"   - TxnType: {txn_type}")
        
        print(f"\n   RAW JSON KEYS:")
        print(f"   {list(tania.raw_json.keys())}")
        
        print(f"\n   FULL RAW JSON:")
        print(json.dumps(tania.raw_json, indent=2))

if __name__ == "__main__":
    pass
