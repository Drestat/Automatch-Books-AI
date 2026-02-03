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
app = modal.App("check-for-review")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_for_review():
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
    
    # Get all transactions that should be "For Review" (is_qbo_matched = False)
    for_review_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.is_qbo_matched == False,
        Transaction.is_excluded == False
    ).order_by(Transaction.date.desc()).all()
    
    print(f"\n{'='*140}")
    print(f"FOR REVIEW TRANSACTIONS IN DATABASE ({len(for_review_txs)} total)")
    print(f"{'='*140}\n")
    
    for tx in for_review_txs:
        date_str = tx.date.strftime("%m/%d/%Y") if tx.date else "N/A"
        print(f"✓ {date_str} | {tx.description[:30]:30} | ${tx.amount:8.2f} | {tx.suggested_category_name or 'No Category'}")
    
    print(f"\n{'='*140}")
    print(f"CHECKING FOR SPECIFIC QBO TRANSACTIONS")
    print(f"{'='*140}\n")
    
    # Check for the specific transactions shown in the QBO screenshot
    qbo_transactions = [
        ("Bob's Burger", "01/06/2026", 18.97),
        ("Norton Lumber", "01/01/2026", 103.55),
        ("Squeaky Kleen", "01/06/2026", 19.99),
        ("Squeaky Kleen", "01/13/2026", 19.99),
        ("Tania's Nursery", "12/26/2025", 82.45)
    ]
    
    for desc, date_str, amount in qbo_transactions:
        # Parse date
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        
        tx = session.query(Transaction).filter(
            Transaction.realm_id == conn.realm_id,
            Transaction.description.ilike(f"%{desc}%"),
            Transaction.date == date_obj,
            Transaction.amount == amount
        ).first()
        
        if tx:
            status = "For Review" if not tx.is_qbo_matched else "Categorized"
            excluded = " (EXCLUDED)" if tx.is_excluded else ""
            print(f"✅ FOUND: {desc:20} | {date_str} | ${amount:8.2f} | Status: {status}{excluded}")
        else:
            print(f"❌ MISSING: {desc:20} | {date_str} | ${amount:8.2f}")
    
    print(f"\n{'='*140}")
    print(f"ALL MASTERCARD TRANSACTIONS (For Review + Categorized)")
    print(f"{'='*140}\n")
    
    all_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"Total Mastercard transactions: {len(all_txs)}")
    print(f"For Review: {len([t for t in all_txs if not t.is_qbo_matched and not t.is_excluded])}")
    print(f"Categorized: {len([t for t in all_txs if t.is_qbo_matched and not t.is_excluded])}")
    print(f"Excluded: {len([t for t in all_txs if t.is_excluded])}")

if __name__ == "__main__":
    pass
