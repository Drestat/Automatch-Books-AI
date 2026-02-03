import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("verify-linkedtxn-fix")
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
    
    # Find all transactions with "Matched to QBO Entry" category
    matched_txns = session.query(Transaction).filter(
        Transaction.qbo_category_name == "Matched to QBO Entry"
    ).all()
    
    print(f"\n{'='*120}")
    print(f"VERIFICATION: Transactions with 'Matched to QBO Entry'")
    print(f"{'='*120}\n")
    print(f"Found {len(matched_txns)} transactions with 'Matched to QBO Entry' category\n")
    
    if len(matched_txns) == 0:
        print("✅ No transactions found - this might mean the sync hasn't run yet or the category name is different")
        return
    
    print(f"{'Description':<30} | {'Amount':<10} | {'Date':<12} | {'Status':<15}")
    print(f"{'-'*120}")
    
    for_review_count = 0
    categorized_count = 0
    
    for tx in matched_txns[:20]:  # Show first 20
        status = "FOR REVIEW" if not tx.is_qbo_matched else "CATEGORIZED"
        if not tx.is_qbo_matched:
            for_review_count += 1
        else:
            categorized_count += 1
        
        print(f"{tx.description[:30]:<30} | ${tx.amount:<9} | {str(tx.date)[:10]:<12} | {status:<15}")
    
    if len(matched_txns) > 20:
        print(f"... and {len(matched_txns) - 20} more")
    
    print(f"\n{'='*120}")
    print(f"SUMMARY:")
    print(f"  Total 'Matched to QBO Entry': {len(matched_txns)}")
    print(f"  ├─ For Review: {for_review_count}")
    print(f"  └─ Categorized: {categorized_count}")
    print(f"{'='*120}\n")
    
    if for_review_count == len(matched_txns):
        print("✅ SUCCESS: All 'Matched to QBO Entry' transactions are now in 'For Review'!")
    elif for_review_count > 0:
        print(f"⚠️  PARTIAL: {for_review_count}/{len(matched_txns)} are in 'For Review'")
    else:
        print("❌ ISSUE: None of the 'Matched to QBO Entry' transactions are in 'For Review'")

if __name__ == "__main__":
    pass
