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
app = modal.App("inspect-duplicates")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def inspect_duplicates():
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
    print(f"CHECKING FOR DUPLICATES (TxnType 1 vs 54)")
    print(f"{'='*140}\n")
    
    # Check Tania's Nursery
    print("--- Tania's Nursery ---")
    tania_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Tania%")
    ).all()
    
    for tx in tania_txs:
        txn_type = "Unknown"
        purchase_ex = tx.raw_json.get("PurchaseEx", {})
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
        
        print(f"ID: {tx.id} | Date: {tx.date} | Amt: {tx.amount} | Type: {txn_type} | DocNum: {tx.raw_json.get('DocNumber')}")

    # Check Norton Lumber
    print("\n--- Norton Lumber ---")
    norton_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Norton%")
    ).all()
    
    for tx in norton_txs:
        txn_type = "Unknown"
        # Check if BillPayment
        if "VendorRef" in tx.raw_json and ("CheckPayment" in tx.raw_json or "CreditCardPayment" in tx.raw_json):
            txn_type = "BillPayment"
        else:
            purchase_ex = tx.raw_json.get("PurchaseEx", {})
            if "any" in purchase_ex:
                for item in purchase_ex["any"]:
                    if item.get("value", {}).get("Name") == "TxnType":
                        txn_type = item.get("value", {}).get("Value")
        
        print(f"ID: {tx.id} | Date: {tx.date} | Amt: {tx.amount} | Type: {txn_type} | DocNum: {tx.raw_json.get('DocNumber')}")

    # Check Lara's Lamination
    print("\n--- Lara's Lamination ---")
    lara_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.description.ilike("%Lara%")
    ).all()
    
    for tx in lara_txs:
        txn_type = "Unknown"
        purchase_ex = tx.raw_json.get("PurchaseEx", {})
        if "any" in purchase_ex:
            for item in purchase_ex["any"]:
                if item.get("value", {}).get("Name") == "TxnType":
                    txn_type = item.get("value", {}).get("Value")
        
        print(f"ID: {tx.id} | Date: {tx.date} | Amt: {tx.amount} | Type: {txn_type} | DocNum: {tx.raw_json.get('DocNumber')}")

if __name__ == "__main__":
    pass
