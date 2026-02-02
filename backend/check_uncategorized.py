import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-uncategorized")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_uncategorized():
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
    
    print(f"\n{'='*140}")
    print(f"CHECKING FOR 'UNCATEGORIZED EXPENSE' TRANSACTIONS")
    print(f"{'='*140}\n")
    
    uncategorized_txs = []
    for tx in txs:
        if tx.suggested_category_name:
            cat_lower = tx.suggested_category_name.lower()
            if "uncategorized" in cat_lower:
                uncategorized_txs.append(tx)
    
    print(f"Found {len(uncategorized_txs)} transactions with 'Uncategorized' in category name:\n")
    
    print(f"{'Date':<12} | {'Description':<35} | {'Category':<30} | {'is_qbo_matched':<15}")
    print(f"{'-'*140}")
    
    for tx in uncategorized_txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:35]
        cat = (tx.suggested_category_name or "N/A")[:30]
        matched = str(tx.is_qbo_matched)
        print(f"{date_str:<12} | {desc:<35} | {cat:<30} | {matched:<15}")
    
    print(f"\n{'='*140}")
    if uncategorized_txs:
        if all(not tx.is_qbo_matched for tx in uncategorized_txs):
            print("✅ All 'Uncategorized' transactions are correctly marked as For Review (is_qbo_matched=False)")
        else:
            print("⚠️  Some 'Uncategorized' transactions are incorrectly marked as Categorized (is_qbo_matched=True)")
            print("This needs to be fixed!")
    else:
        print("No transactions with 'Uncategorized' in category name found.")

if __name__ == "__main__":
    pass
