import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("list-all-txs")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def list_all_txs():
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
    
    txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).order_by(Transaction.date.desc()).all()
    
    print(f"\n{'='*160}")
    print(f"ALL TRANSACTIONS ({len(txs)})")
    print(f"{'='*160}\n")
    
    print(f"{'Date':<12} | {'Description':<40} | {'Amount':<10} | {'Status':<15} | {'Category'}")
    print(f"{'-'*160}")
    
    for tx in txs:
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        desc = (tx.description or "")[:40]
        amt = f"{tx.amount:.2f}"
        status = "QT (Matched)" if tx.is_qbo_matched else "FR (Review)"
        cat = tx.suggested_category_name or "N/A"
        
        print(f"{date_str:<12} | {desc:<40} | {amt:<10} | {status:<15} | {cat}")

if __name__ == "__main__":
    pass
