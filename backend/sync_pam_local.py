import modal
from dotenv import dotenv_values

app = modal.App("sync-pam-local")
env_vars = dotenv_values(".env")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "pydantic")
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

@app.local_entrypoint()
def main():
    update_local_db.remote()

@app.function(image=image)
def update_local_db():
    from app.models.qbo import Transaction, QBOConnection
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import os

    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Update ID 127 amount to 75.00
        # Check if it exists first
        tx_id = "127"
        txn = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if txn:
            print(f"Updating Local Transaction {tx_id} from {txn.amount} to 75.00")
            txn.amount = 75.00
            
            # Also update raw_json to reflect change if we want consistency, 
            # though app uses columns usually.
            if txn.raw_json:
                import json
                # It's stored as JSON/dict
                # raw_json is likely a dict or list?
                # It's a dict in model.
                # Use standard dict access
                try:
                    # txn.raw_json is a MutableDict or similar with SQLAlchemy?
                    # Or just a dict.
                    # We might need to copy, modify, set back to trigger change if JSON type.
                    data = dict(txn.raw_json)
                    data['TotalAmt'] = 75.00
                    # Update line 0 too if present
                    if 'Line' in data and len(data['Line']) > 0:
                        if 'Amount' in data['Line'][0]:
                             data['Line'][0]['Amount'] = 75.00
                    
                    txn.raw_json = data
                except Exception as e:
                    print(f"Failed to update raw_json: {e}")

            db.commit()
            print("Local DB Updated successfully.")
        else:
            print(f"Transaction {tx_id} not found locally.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
