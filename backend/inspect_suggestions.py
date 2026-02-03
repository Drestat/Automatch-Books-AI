import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-suggestions")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_suggestions():
    from sqlalchemy import create_engine, or_
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    import json
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    search_terms = ["Bob's Burger", "Squeaky Kleen", "Tania's Nursery", "Norton Lumber"]
    filters = [Transaction.description.ilike(f"%{term}%") for term in search_terms]
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        or_(*filters)
    ).all()
    
    print(f"\n{'='*140}")
    print(f"SUGGESTION INSPECTION ({len(txs)} transactions)")
    print(f"{'='*140}\n")
    
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        print(f"ID: {tx.id} | Description: {tx.description}")
        print(f"Date: {date_str} | Amount: {tx.amount}")
        print(f"Category: {tx.suggested_category_name}")
        print(f"Status: {'Matched/Categorized' if tx.is_qbo_matched else 'For Review'}")
        
        # Extract TxnType
        purchase_ex = tx.raw_json.get("PurchaseEx", {})
        txn_type = "Not Found"
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    break
        print(f"TxnType: {txn_type}")
        
        # Check LinkedTxn in Line
        line = tx.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        print(f"Has LinkedTxn (Line): {has_linked}")
        
        # Check top-level LinkedTxn (sometimes exists for BillPayment)
        has_top_linked = "LinkedTxn" in tx.raw_json
        print(f"Has LinkedTxn (Top): {has_top_linked}")

        # Search for ANY 'Match' or 'Suggestion' keywords in raw_json
        raw_str = json.dumps(tx.raw_json).lower()
        print(f"Keywords Found: {'match' in raw_str}, {'suggest' in raw_str}, {'feed' in raw_str}")
        
        print(f"TxnSource: {tx.raw_json.get('TxnSource')}")
        
        print("\nRAW JSON KEYS:")
        print(list(tx.raw_json.keys()))
        print(f"{'-'*140}\n")

if __name__ == "__main__":
    pass
