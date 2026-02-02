import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-categorized")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_categorized():
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
    print(f"CATEGORIZATION STATUS AFTER SYNC")
    print(f"{'='*140}\n")
    
    categorized = [tx for tx in txs if tx.is_qbo_matched]
    for_review = [tx for tx in txs if not tx.is_qbo_matched and not tx.is_excluded]
    
    print(f"Total Mastercard transactions: {len(txs)}")
    print(f"Categorized (is_qbo_matched=True): {len(categorized)}")
    print(f"For Review (is_qbo_matched=False): {len(for_review)}\n")
    
    print(f"{'='*140}")
    print(f"CATEGORIZED TRANSACTIONS")
    print(f"{'='*140}\n")
    print(f"{'Date':<12} | {'Description':<35} | {'Category':<30}")
    print(f"{'-'*140}")
    
    for tx in categorized:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:35]
        cat = (tx.suggested_category_name or "N/A")[:30]
        print(f"{date_str:<12} | {desc:<35} | {cat:<30}")
    
    print(f"\n{'='*140}")
    print(f"FOR REVIEW TRANSACTIONS")
    print(f"{'='*140}\n")
    print(f"{'Date':<12} | {'Description':<35} | {'Category':<30}")
    print(f"{'-'*140}")
    
    for tx in for_review:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:35]
        cat = (tx.suggested_category_name or "N/A")[:30]
        print(f"{date_str:<12} | {desc:<35} | {cat:<30}")

if __name__ == "__main__":
    pass
