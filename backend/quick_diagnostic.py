import modal
import os
from dotenv import dotenv_values

# 1. Setup similar to modal_app.py to ensure environment parity
base_dir = os.path.dirname(os.path.abspath(__file__))
# Check if .env is in backend/ or root
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi", 
        "uvicorn", 
        "psycopg2-binary", 
        "pydantic-settings", 
        "python-dotenv",
        "sqlalchemy",
        "intuit-oauth",
        "requests",
        "google-generativeai",
        "stripe",
        "rapidfuzz",
        "python-multipart",
        "pytz",
        "alembic"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

app = modal.App("quick-diagnostic-tool")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def show_db_state():
    # Defer imports to run ONLY inside the Modal container
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    from datetime import datetime, timezone, timedelta
    
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("====================================================================================================")
    print("CURRENT DATABASE STATE - ELEGANT ARCHITECTURE VERIFICATION")
    print("====================================================================================================")
    
    # 1. Check Total Count
    txs = db.query(Transaction).all()
    print(f"\nTotal Transactions in DB: {len(txs)}")
    
    if len(txs) == 0:
        print("⚠️  Database is empty. Wating for sync...")
        return

    # 2. Detail View for Logic Verification
    print(f"\n{'Desc':<20} | {'Sugg. Cat':<30} | {'DB Status':<12} | {'Legacy(Acct)':<15} | {'COMPUTED STATUS'}")
    print("-" * 115)
    
    for tx in txs:
        # EXACT LOGIC FROM transactions.py
        expense_acc_name = (tx.suggested_category_name or "").lower()
        
        is_uncategorized_account = (
            "uncategorized" in expense_acc_name 
            or "ask my accountant" in expense_acc_name
            or not tx.suggested_category_name 
        )
        
        computed_status = "CATEGORIZED"
        if is_uncategorized_account:
            computed_status = "NEEDS_REVIEW"
            
        # Logging
        desc = (tx.description or "No Desc")[:20]
        cat = (tx.suggested_category_name or "None")[:30]
        db_status = (tx.status or "None")[:12]
        bank_acc = (tx.account_name or "None")[:15]
        
        print(f"{desc:<20} | {cat:<30} | {db_status:<12} | {bank_acc:<15} | {computed_status}")

if __name__ == "__main__":
    # Local verification to ensure it can run
    pass
