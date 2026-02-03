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
app = modal.App("inspect-squeaky-0113")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_squeaky_0113():
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
    
    # Search for Squeaky Kleen on 01/13/2026
    target_date = datetime(2026, 1, 13)
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Squeaky Kleen%"),
        Transaction.date == target_date
    ).all()
    
    print(f"\n{'='*140}")
    print(f"SQUEAKY KLEEN 01/13/2026 INSPECTION")
    print(f"{'='*140}\n")
    
    for tx in txs:
        print(f"✅ FOUND: ID {tx.id}")
        print(f"Description: {tx.description}")
        print(f"Date: {tx.date}")
        print(f"Amount: ${tx.amount}")
        print(f"Category: {tx.suggested_category_name}")
        print(f"Status: {'Categorized' if tx.is_qbo_matched else 'For Review'}")
        print(f"\nRAW JSON ANALYSIS:")
        
        # Check for DocNumber
        doc_number = tx.raw_json.get("DocNumber")
        print(f"  DocNumber: {doc_number if doc_number else '(None)'}")
        
        # Check for LinkedTxn
        line = tx.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        print(f"  Has LinkedTxn: {has_linked}")
        
        # Check TxnType
        purchase_ex = tx.raw_json.get("PurchaseEx", {})
        txn_type = "Not Found"
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    break
        print(f"  TxnType: {txn_type}")
        
        # Check EntityRef (Payee)
        entity_ref = tx.raw_json.get("EntityRef", {})
        payee = entity_ref.get("name", "(None)")
        print(f"  Payee (EntityRef): {payee}")
        
        # Check AccountRef (Category)
        lines = tx.raw_json.get("Line", [])
        for line in lines:
            if "AccountBasedExpenseLineDetail" in line:
                acc_ref = line["AccountBasedExpenseLineDetail"].get("AccountRef", {})
                print(f"  Category (AccountRef): {acc_ref.get('name', '(None)')}")
        
        print(f"\n🔍 WHY IS IT 'FOR REVIEW'?")
        print(f"  - DocNumber: {'❌ MISSING' if not doc_number else '✅ Present'}")
        print(f"  - LinkedTxn: {'❌ MISSING' if not has_linked else '✅ Present'}")
        print(f"  → Result: {'FOR REVIEW (no DocNumber or LinkedTxn)' if not (doc_number or has_linked) else 'CATEGORIZED'}")
        
        print(f"\n📋 FULL RAW JSON:")
        print(json.dumps(tx.raw_json, indent=2))

if __name__ == "__main__":
    pass
