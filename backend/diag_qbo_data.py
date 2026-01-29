import modal
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient
import json
import os
from dotenv import dotenv_values

stub = modal.App("qbo-diag")

# Load local env for secrets
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = dotenv_values(env_path)
secrets = modal.Secret.from_dict(env_vars)

# Define the image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "requests", "pydantic", "intuit-oauth", "python-dotenv", "pydantic-settings")
    .add_local_dir("./app", remote_path="/root/app")
)

@stub.function(image=image, secrets=[secrets])
def inspect_qbo_data(realm_id: str):
    print(f"--- DB CHECK START for Realm: {realm_id} ---")
    
    db = SessionLocal()
    try:
        # Check Transaction Table count
        from app.models.qbo import Transaction
        count = db.query(Transaction).filter(Transaction.realm_id == realm_id).count()
        print(f"Total Transactions in DB: {count}")
        
        if count > 0:
            txs = db.query(Transaction).filter(Transaction.realm_id == realm_id).limit(3).all()
            for t in txs:
                print(f" - Tx: {t.description} | Amt: {t.amount} | AcctID: {t.account_id} | AcctName: {t.account_name}")
        else:
            print("DB is EMPTY. Sync didn't work or hasn't finished.")

    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
    finally:
        db.close()
        print("--- DB CHECK END ---")

if __name__ == "__main__":
    # Hardcoded Realm ID from user's URL
    with stub.run():
        inspect_qbo_data.remote("9341456245321396")
