import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("analyze-raw-json")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def analyze_raw_json():
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
    
    # Get specific transactions from screenshot
    target_descriptions = ["Squeaky Kleen", "Bob's Burger", "Norton Lumber", "Tania's Nursery"]
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).all()
    
    print(f"\n{'='*140}")
    print(f"ANALYZING RAW JSON STRUCTURE")
    print(f"{'='*140}\n")
    
    for tx in txs:
        if any(desc in (tx.description or "") for desc in target_descriptions):
            print(f"\n{'='*140}")
            print(f"Transaction: {tx.description} ({tx.date.strftime('%Y-%m-%d')})")
            print(f"Suggested Category: {tx.suggested_category_name}")
            print(f"is_qbo_matched: {tx.is_qbo_matched}")
            print(f"{'='*140}")
            
            if tx.raw_json:
                # Check for LinkedTxn
                has_linked = False
                if "Line" in tx.raw_json:
                    for line in tx.raw_json["Line"]:
                        if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                            has_linked = True
                            print(f"✅ Has LinkedTxn: {line['LinkedTxn']}")
                            break
                
                if not has_linked:
                    print(f"❌ No LinkedTxn")
                
                # Check Line details
                if "Line" in tx.raw_json:
                    for i, line in enumerate(tx.raw_json["Line"]):
                        print(f"\nLine {i}:")
                        
                        # Account-based expense line
                        if "AccountBasedExpenseLineDetail" in line:
                            detail = line["AccountBasedExpenseLineDetail"]
                            print(f"  Type: AccountBasedExpenseLineDetail")
                            if "AccountRef" in detail:
                                print(f"  AccountRef: {detail['AccountRef']}")
                            if "ClassRef" in detail:
                                print(f"  ClassRef: {detail['ClassRef']}")
                        
                        # Item-based expense line
                        if "ItemBasedExpenseLineDetail" in line:
                            detail = line["ItemBasedExpenseLineDetail"]
                            print(f"  Type: ItemBasedExpenseLineDetail")
                            if "ItemRef" in detail:
                                print(f"  ItemRef: {detail['ItemRef']}")
                
                # Print full JSON for one example
                if "Bob" in tx.description:
                    print(f"\n{'='*140}")
                    print(f"FULL RAW JSON FOR BOB'S BURGER:")
                    print(f"{'='*140}")
                    print(json.dumps(tx.raw_json, indent=2))

if __name__ == "__main__":
    pass
