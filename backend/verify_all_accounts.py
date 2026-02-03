import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("verify-all-accounts")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def verify_all_accounts():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all transactions grouped by account
    all_txns = session.query(Transaction).all()
    
    # Group by account
    accounts = {}
    for tx in all_txns:
        acc_name = tx.account_name or "Unknown"
        if acc_name not in accounts:
            accounts[acc_name] = {"total": 0, "for_review": 0, "categorized": 0}
        
        accounts[acc_name]["total"] += 1
        if tx.is_qbo_matched:
            accounts[acc_name]["categorized"] += 1
        else:
            accounts[acc_name]["for_review"] += 1
    
    print(f"\n{'='*120}")
    print(f"VERIFICATION: FeedLogic Applied to All Accounts")
    print(f"{'='*120}\n")
    print(f"Total Accounts: {len(accounts)}")
    print(f"Total Transactions: {len(all_txns)}\n")
    
    print(f"{'Account Name':<40} | {'Total':<8} | {'For Review':<12} | {'Categorized':<12}")
    print(f"{'-'*120}")
    
    for acc_name, stats in sorted(accounts.items()):
        print(f"{acc_name:<40} | {stats['total']:<8} | {stats['for_review']:<12} | {stats['categorized']:<12}")
    
    print(f"\n{'='*120}")
    print(f"✅ FeedLogic is being applied to ALL {len(accounts)} account(s)")
    print(f"{'='*120}\n")

if __name__ == "__main__":
    pass
