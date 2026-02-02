import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-all-categories")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_all_categories():
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
    
    print(f"\n{'='*160}")
    print(f"ALL MASTERCARD TRANSACTIONS WITH CATEGORIES")
    print(f"{'='*160}\n")
    
    print(f"{'Date':<12} | {'Description':<35} | {'Category':<40} | {'is_qbo_matched':<15}")
    print(f"{'-'*160}")
    
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:35]
        cat = (tx.suggested_category_name or "NONE")[:40]
        matched = "✅ Categorized" if tx.is_qbo_matched else "❌ For Review"
        print(f"{date_str:<12} | {desc:<35} | {cat:<40} | {matched:<15}")
    
    print(f"\n{'='*160}")
    print(f"SUMMARY")
    print(f"{'='*160}")
    
    categorized = sum(1 for tx in txs if tx.is_qbo_matched)
    for_review = sum(1 for tx in txs if not tx.is_qbo_matched)
    
    print(f"Total: {len(txs)}")
    print(f"Categorized: {categorized}")
    print(f"For Review: {for_review}")

if __name__ == "__main__":
    pass
