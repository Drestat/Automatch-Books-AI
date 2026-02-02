import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("add-column-and-sync")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets], timeout=300)
def add_column_and_sync():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    from app.services.transaction_service import TransactionService
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n{'='*140}")
    print(f"STEP 1: Adding is_bank_feed_import column")
    print(f"{'='*140}\n")
    
    try:
        # Add column if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE transactions 
                ADD COLUMN IF NOT EXISTS is_bank_feed_import BOOLEAN DEFAULT true
            """))
            conn.commit()
        print("✅ Column added successfully!")
    except Exception as e:
        print(f"⚠️  Column might already exist: {e}")
    
    print(f"\n{'='*140}")
    print(f"STEP 2: Running sync to populate is_bank_feed_import")
    print(f"{'='*140}\n")
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    # Run sync
    service = TransactionService(session, conn)
    service.sync_transactions()
    
    print(f"\n{'='*140}")
    print(f"STEP 3: Verifying results")
    print(f"{'='*140}\n")
    
    # Count transactions
    mastercard_txs = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).all()
    
    bank_feed_count = sum(1 for tx in mastercard_txs if tx.is_bank_feed_import)
    manual_count = sum(1 for tx in mastercard_txs if not tx.is_bank_feed_import)
    
    print(f"Total Mastercard transactions: {len(mastercard_txs)}")
    print(f"Bank feed imports: {bank_feed_count}")
    print(f"Manual entries (TxnType=54): {manual_count}")
    print(f"\n✅ Frontend should now show {bank_feed_count} transactions (matching QBO Banking)")

if __name__ == "__main__":
    pass
