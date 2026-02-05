import modal
import os
from dotenv import dotenv_values
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "httpx", "intuit-oauth")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)
app = modal.App("test-clrstatus-modal")
secrets = modal.Secret.from_dict({
    "DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_CLIENT_SECRET", ""),
    "QBO_ENVIRONMENT": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_ENVIRONMENT", "sandbox"),
    "QBO_REDIRECT_URI": dotenv_values(os.path.join(base_dir, ".env")).get("QBO_REDIRECT_URI", "")
})

@app.function(image=image, secrets=[secrets])
async def test_update():
    from app.db.session import SessionLocal
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = SessionLocal()
    conn = db.query(QBOConnection).first()
    client = QBOClient(db, conn)
    
    # Use ID 152 (Unmatched A1 Rental in previous dump)
    tx_id = "152"
    
    # 1. Fetch current
    current = await client.request("GET", f"purchase/{tx_id}")
    p = current.get("Purchase", {})
    sync_token = p.get("SyncToken")
    
    print(f"Original SyncToken: {sync_token}")
    
    # 2. Try to update with ClrStatus (if possible)
    # We'll try at the top level and in lines
    update_payload = {
        "Id": tx_id,
        "SyncToken": sync_token,
        "sparse": True,
        "ClrStatus": "Cleared",
        "Line": [
            {
                "Id": "1",
                "DetailType": "AccountBasedExpenseLineDetail",
                "AccountBasedExpenseLineDetail": {
                    "ClrStatus": "Cleared"
                }
            }
        ]
    }
    
    try:
        print("Trying update with ClrStatus...")
        res = await client.request("POST", "purchase", json_payload=update_payload)
        print("Success!")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Failed to update ClrStatus: {e}")
        
    db.close()

if __name__ == "__main__":
    pass
