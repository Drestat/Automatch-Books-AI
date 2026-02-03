import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-hicks")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_hicks():
    from sqlalchemy import create_engine
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
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Hicks Hardware%")
    ).all()
    
    print(f"\n{'='*140}")
    print(f"HICKS HARDWARE TRANSACTIONS ({len(txs)})")
    print(f"{'='*140}\n")
    
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        print(f"ID: {tx.id}")
        print(f"Date: {date_str}")
        print(f"Amount: {tx.amount}")
        print(f"Category: {tx.suggested_category_name}")
        print(f"Status: {'Matched/Categorized' if tx.is_qbo_matched else 'For Review'}")
        
        # Extract TxnType from raw_json
        purchase_ex = tx.raw_json.get("PurchaseEx", {})
        txn_type = "Not Found"
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
                    break
        print(f"TxnType: {txn_type}")
        
        # Check LinkedTxn
        line = tx.raw_json.get("Line", [])
        has_linked = any("LinkedTxn" in l for l in line)
        print(f"Has LinkedTxn: {has_linked}")
        
        print("\nRAW JSON (Header):")
        # Print only top level keys for brevity
        header = {k: v for k, v in tx.raw_json.items() if k != "Line"}
        print(json.dumps(header, indent=2))
        print(f"{'-'*140}\n")

if __name__ == "__main__":
    pass
