import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("analyze-mastercard")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def analyze_visibility():
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
    
    # Get all Mastercard transactions
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"\n{'='*120}")
    print(f"MASTERCARD TRANSACTION VISIBILITY ANALYSIS")
    print(f"{'='*120}\n")
    print(f"Total Mastercard Transactions in DB: {len(txs)}\n")
    
    # Group by status
    by_matched = {"Matched (LinkedTxn)": [], "For Review (No Link)": []}
    
    for tx in txs:
        if tx.is_qbo_matched:
            by_matched["Matched (LinkedTxn)"].append(tx)
        else:
            by_matched["For Review (No Link)"].append(tx)
    
    print(f"📊 BREAKDOWN:")
    print(f"  - Matched/Added (has LinkedTxn): {len(by_matched['Matched (LinkedTxn)'])}")
    print(f"  - For Review (no LinkedTxn): {len(by_matched['For Review (No Link)'])}\n")
    
    print(f"{'='*120}")
    print(f"MATCHED TRANSACTIONS (These moved to your Books in QBO)")
    print(f"{'='*120}")
    print(f"{'Date':<12} | {'Description':<30} | {'Amount':<10} | {'Category':<40}")
    print(f"{'-'*120}")
    
    for tx in by_matched["Matched (LinkedTxn)"]:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:30]
        amt = f"${tx.amount:.2f}" if tx.amount else "N/A"
        cat = (tx.suggested_category_name or "None")[:40]
        print(f"{date_str:<12} | {desc:<30} | {amt:<10} | {cat:<40}")
    
    print(f"\n{'='*120}")
    print(f"FOR REVIEW TRANSACTIONS (These should be visible in QBO Banking)")
    print(f"{'='*120}")
    print(f"{'Date':<12} | {'Description':<30} | {'Amount':<10} | {'Category':<40}")
    print(f"{'-'*120}")
    
    for tx in by_matched["For Review (No Link)"]:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:30]
        amt = f"${tx.amount:.2f}" if tx.amount else "N/A"
        cat = (tx.suggested_category_name or "None")[:40]
        print(f"{date_str:<12} | {desc:<30} | {amt:<10} | {cat:<40}")
    
    print(f"\n{'='*120}")
    print(f"WHERE TO FIND MATCHED TRANSACTIONS IN QBO:")
    print(f"{'='*120}")
    print(f"1. Go to 'Expenses' (left sidebar)")
    print(f"2. Filter by 'Mastercard' account")
    print(f"3. You should see the {len(by_matched['Matched (LinkedTxn)'])} matched transactions there")
    print(f"\nThese transactions are NO LONGER in the Banking tab because you already added them!")

if __name__ == "__main__":
    pass
