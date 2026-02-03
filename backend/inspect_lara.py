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
app = modal.App("inspect-lara")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_lara():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    from datetime import datetime
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    print(f"\n{'='*140}")
    print(f"INSPECTING LARA'S LAMINATION")
    print(f"{'='*140}\n")
    
    # Search for Lara's Lamination
    lara = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Lara%")
    ).first()
    
    if lara:
        print(f"✅ FOUND: ID {lara.id}")
        print(f"Description: {lara.description}")
        print(f"Date: {lara.date}")
        print(f"Amount: ${lara.amount}")
        print(f"Status: {'Categorized' if lara.is_qbo_matched else 'For Review'}")
        
        # Check signals
        doc_number = lara.raw_json.get("DocNumber")
        line = lara.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        
        # Check TxnType
        purchase_ex = lara.raw_json.get("PurchaseEx", {})
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
        
        print(f"\n   FULL RAW JSON:")
        print(json.dumps(lara.raw_json, indent=2))
        
    else:
        print("❌ Lara's Lamination NOT FOUND in database")

if __name__ == "__main__":
    pass
