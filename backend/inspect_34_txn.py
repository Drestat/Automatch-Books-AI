import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("inspect-34-txn")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_34_txn():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    import json
    from datetime import datetime
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Logic to find the transaction
    # Date: 2026-01-26
    # Amount: 34.00
    
    target_date = "2026-01-26"
    target_amount = 34.00
    
    print(f"\n{'='*140}")
    print(f"SEARCHING FOR TRANSACTION: {target_date} / ${target_amount}")
    print(f"{'='*140}\n")
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.amount == target_amount
    ).all()
    
    found = False
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        if date_str == target_date:
            found = True
            print(f"✅ FOUND TRANSACTION: {tx.id}")
            print(f"   Description: {tx.description}")
            print(f"   Category: {tx.suggested_category_name}")
            print(f"   Status: {'Matched' if tx.is_qbo_matched else 'For Review'}")
            print(f"   Note: {tx.note}")
            
            print(f"\n   RAW JSON:")
            print(json.dumps(tx.raw_json, indent=2))
            
            # Check for "Automobile" in JSON
            json_str = json.dumps(tx.raw_json)
            if "Automobile" in json_str:
                print(f"\n   🔎 'Automobile' FOUND in JSON data!")
            else:
                print(f"\n   ❌ 'Automobile' NOT found in JSON data.")
                
            break
            
    if not found:
        print("❌ Transaction not found in database.")

if __name__ == "__main__":
    pass
