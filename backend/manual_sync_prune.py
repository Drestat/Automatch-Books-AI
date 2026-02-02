import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "requests", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("manual-sync-prune")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets], timeout=300)
def manual_sync():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import QBOConnection, Transaction
    from app.services.transaction_service import TransactionService
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    conn = session.query(QBOConnection).first()
    if not conn:
        print("No connection found")
        return
    
    print(f"\n{'='*140}")
    print(f"BEFORE SYNC: Database State")
    print(f"{'='*140}\n")
    
    # Count transactions before sync
    before_count = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).count()
    
    print(f"Mastercard transactions in DB: {before_count}\n")
    
    print(f"{'='*140}")
    print(f"RUNNING SYNC...")
    print(f"{'='*140}\n")
    
    # Run sync
    service = TransactionService(session, conn)
    service.sync_transactions()
    
    print(f"\n{'='*140}")
    print(f"AFTER SYNC: Database State")
    print(f"{'='*140}\n")
    
    # Count transactions after sync
    after_count = session.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.account_name.ilike("%mastercard%")
    ).count()
    
    print(f"Mastercard transactions in DB: {after_count}")
    print(f"Pruned: {before_count - after_count} transactions\n")
    
    if before_count - after_count > 0:
        print(f"✅ Successfully pruned {before_count - after_count} stale transactions!")
        print(f"The app should now match QBO's Banking tab.")
    else:
        print(f"⚠️  No transactions were pruned. This suggests:")
        print(f"1. All 16 transactions still exist in QBO (unlikely based on user screenshot)")
        print(f"2. The sync query is not returning the correct data")
        print(f"3. There's a bug in the pruning logic")

if __name__ == "__main__":
    pass
