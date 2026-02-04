import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("check-db-state-modal")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def check_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.qbo import Transaction, BankAccount
    import os
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all transactions
    all_txs = session.query(Transaction).all()
    print(f"📊 Total transactions in DB: {len(all_txs)}\n")
    
    # Group by account_id
    by_account = {}
    for tx in all_txs:
        acc_id = tx.account_id or "NULL"
        if acc_id not in by_account:
            by_account[acc_id] = []
        by_account[acc_id].append(tx)
    
    print("Transactions by account_id:")
    for acc_id, txs in sorted(by_account.items()):
        print(f"  Account {acc_id}: {len(txs)} transactions")
    
    print("\n" + "="*80)
    
    # Get all bank accounts
    accounts = session.query(BankAccount).all()
    print(f"\n📋 Bank Accounts in DB:")
    for acc in accounts:
        print(f"  ID: {acc.id} | Name: {acc.name} | Active: {acc.is_active} | Connected: {acc.is_connected}")
    
    print("\n" + "="*80)
    
    # Show sample transactions
    print("\n📝 Sample Transactions:")
    for tx in all_txs[:10]:
        print(f"ID: {tx.id} | Account: {tx.account_id} | Amount: ${tx.amount} | Date: {tx.date}")
        print(f"  Description: {tx.description}")
        print(f"  Matched: {tx.is_qbo_matched} | Status: {tx.status}")
        print()

if __name__ == "__main__":
    pass
