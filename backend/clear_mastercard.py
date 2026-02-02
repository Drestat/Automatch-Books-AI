"""
Clear Mastercard transactions to force a fresh sync with the new filter logic
"""
import modal
import os
from dotenv import dotenv_values
from modal import Image

base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

image = Image.debian_slim(python_version="3.9").pip_install(
    "sqlalchemy",
    "psycopg2-binary",
    "python-dotenv",
    "pydantic-settings"
).add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")

app = modal.App("clear-mastercard")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def clear_mastercard_transactions():
    """Delete all Mastercard transactions to force a fresh sync"""
    from app.db.session import get_db
    from app.models.qbo import Transaction
    
    db = next(get_db())
    try:
        print("\n🗑️  Deleting all Mastercard (Account ID 41) transactions...")
        
        count = db.query(Transaction).filter(Transaction.account_id == "41").delete()
        db.commit()
        
        print(f"✅ Deleted {count} transactions")
        print("\n📝 Next step: Disconnect and reconnect QBO in the app to trigger a fresh sync.")
        print("   The new sync will apply the filter logic and only save the 7 real transactions.")
        
    finally:
        db.close()
