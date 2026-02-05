import modal
import asyncio
from dotenv import dotenv_values
import os
import json

# Load env variables for local execution context (secrets will be handled by Modal)
env_vars = dotenv_values(".env")

# Define the image
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
        "httpx",
        "google-generativeai",
        "stripe",
        "rapidfuzz",
        "python-multipart",
        "pytz",
        "alembic"
    )
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

app = modal.App("test-qbo-update")

@app.local_entrypoint()
def main():
    test_update.remote()

@app.function(image=image)
async def test_update():
    import sys
    sys.path.append("/root")
    from app.services.qbo_client import QBOClient
    from app.models.qbo import QBOConnection
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        # Get the first connection (assuming only one user or specific realm)
        connection = db.query(QBOConnection).first()
        if not connection:
            print("❌ No QBO Connection found.")
            return

        client = QBOClient(db, connection)
        
        # Target Transaction ID 127 (Pam Seitz)
        tx_id = "127"
        
        # Fetch current state to get SyncToken and PaymentType
        print(f"📡 Fetching transaction {tx_id}...")
        current_tx = await client.get_purchase(tx_id)
        current_purchase = current_tx.get("Purchase")
        sync_token = current_purchase.get("SyncToken")
        payment_type = current_purchase.get("PaymentType")
        
        print(f"✅ Current SyncToken: {sync_token}")
        print(f"✅ PaymentType: {payment_type}")
        print(json.dumps(current_purchase, indent=2))


    finally:
        db.close()
