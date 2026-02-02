import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("find-missing-9")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def find_missing():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    import os
    from datetime import datetime, timezone
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Get all Mastercard transactions
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"\n{'='*140}")
    print(f"FINDING THE 9 'MISSING' TRANSACTIONS")
    print(f"{'='*140}\n")
    print(f"Total in App: {len(txs)}")
    print(f"Total in QBO Banking: 7")
    print(f"Missing: {len(txs) - 7} = 9 transactions\n")
    
    # Check raw_json for LinkedTxn
    print(f"{'Date':<12} | {'Description':<30} | {'Amount':<10} | {'Has LinkedTxn':<15} | {'Category':<40}")
    print(f"{'-'*140}")
    
    has_link_count = 0
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:30]
        amt = f"${tx.amount:.2f}" if tx.amount else "N/A"
        cat = (tx.suggested_category_name or "None")[:40]
        
        # Check raw JSON for LinkedTxn
        has_linked = False
        if tx.raw_json and "Line" in tx.raw_json:
            for line in tx.raw_json["Line"]:
                if "LinkedTxn" in line and len(line["LinkedTxn"]) > 0:
                    has_linked = True
                    has_link_count += 1
                    break
        
        marker = "✅ ADDED" if has_linked else "❌ FOR REVIEW"
        print(f"{date_str:<12} | {desc:<30} | {amt:<10} | {marker:<15} | {cat:<40}")
    
    print(f"\n{'='*140}")
    print(f"HYPOTHESIS:")
    print(f"{'='*140}")
    print(f"Transactions with '✅ ADDED' have LinkedTxn → Already in your Books (not in Banking tab)")
    print(f"Transactions with '❌ FOR REVIEW' should be visible in QBO Banking")
    print(f"\nIf {has_link_count} transactions have LinkedTxn, then {len(txs) - has_link_count} should be in Banking.")
    print(f"You said you see 7 in QBO Banking.")
    print(f"\nDISCREPANCY: {len(txs) - has_link_count} (expected) vs 7 (actual)")
    
    if len(txs) - has_link_count != 7:
        print(f"\n⚠️  MISMATCH! Let me check for other reasons...")
        print(f"\nPossible causes:")
        print(f"1. QBO has a date filter active (check 'All dates' dropdown)")
        print(f"2. Some transactions were 'Excluded' in QBO")
        print(f"3. QBO is showing a different account")

if __name__ == "__main__":
    pass
