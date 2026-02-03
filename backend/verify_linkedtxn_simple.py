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
app = modal.App("verify-linkedtxn-simple")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def verify_linkedtxn():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all transactions
    all_txns = session.query(Transaction).all()
    
    # Find transactions with LinkedTxn
    linkedtxn_txns = []
    for tx in all_txns:
        raw = tx.raw_json
        has_linked = False
        for line in raw.get("Line", []):
            if "LinkedTxn" in line and line["LinkedTxn"]:
                has_linked = True
                break
        if has_linked:
            linkedtxn_txns.append(tx)
    
    print(f"\n{'='*120}")
    print(f"VERIFICATION: Transactions with LinkedTxn")
    print(f"{'='*120}\n")
    print(f"Total transactions: {len(all_txns)}")
    print(f"Transactions with LinkedTxn: {len(linkedtxn_txns)}\n")
    
    if len(linkedtxn_txns) == 0:
        print("✅ No transactions with LinkedTxn found")
        return
    
    print(f"{'Description':<30} | {'Amount':<10} | {'Date':<12} | {'Status':<15}")
    print(f"{'-'*120}")
    
    for_review_count = 0
    categorized_count = 0
    
    for tx in linkedtxn_txns:
        status = "FOR REVIEW" if not tx.is_qbo_matched else "CATEGORIZED"
        if not tx.is_qbo_matched:
            for_review_count += 1
        else:
            categorized_count += 1
        
        print(f"{tx.description[:30]:<30} | ${tx.amount:<9} | {str(tx.date)[:10]:<12} | {status:<15}")
    
    print(f"\n{'='*120}")
    print(f"SUMMARY:")
    print(f"  Total with LinkedTxn: {len(linkedtxn_txns)}")
    print(f"  ├─ For Review: {for_review_count}")
    print(f"  └─ Categorized: {categorized_count}")
    print(f"{'='*120}\n")
    
    if for_review_count == len(linkedtxn_txns):
        print("✅ SUCCESS: All LinkedTxn transactions are now in 'For Review'!")
    elif for_review_count > 0:
        print(f"⚠️  PARTIAL: {for_review_count}/{len(linkedtxn_txns)} are in 'For Review'")
    else:
        print("❌ ISSUE: None of the LinkedTxn transactions are in 'For Review'")

if __name__ == "__main__":
    pass
