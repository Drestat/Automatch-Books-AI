import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-txn-types")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_txn_types():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Get specific transactions from screenshot
    target_descriptions = ["Squeaky Kleen", "Bob's Burger", "Norton Lumber", "Tania's Nursery"]
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).all()
    
    print(f"\n{'='*160}")
    print(f"TRANSACTION TYPES AND SOURCES")
    print(f"{'='*160}\n")
    
    print(f"{'Date':<12} | {'Description':<30} | {'TxnType':<10} | {'Source':<20} | {'Category':<40}")
    print(f"{'-'*160}")
    
    for tx in txs:
        if any(desc in (tx.description or "") for desc in target_descriptions):
            date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
            desc = (tx.description or "")[:30]
            cat = (tx.suggested_category_name or "NONE")[:40]
            
            # Get TxnType from raw_json
            txn_type = "N/A"
            if tx.raw_json and "PurchaseEx" in tx.raw_json:
                purchase_ex = tx.raw_json.get("PurchaseEx", {})
                if "any" in purchase_ex:
                    for item in purchase_ex["any"]:
                        if item.get("value", {}).get("Name") == "TxnType":
                            txn_type = item.get("value", {}).get("Value", "N/A")
                            break
            
            source = "Manual Entry" if txn_type == "54" else "Bank Feed"
            
            print(f"{date_str:<12} | {desc:<30} | {txn_type:<10} | {source:<20} | {cat:<40}")
    
    print(f"\n{'='*160}")
    print(f"KEY:")
    print(f"  TxnType=1 or 11: Bank feed import")
    print(f"  TxnType=54: Manual entry")
    print(f"{'='*160}")

if __name__ == "__main__":
    pass
