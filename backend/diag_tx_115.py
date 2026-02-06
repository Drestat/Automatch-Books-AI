import modal
import os
from dotenv import dotenv_values

# 1. Capture production keys from disk
base_dir = os.path.dirname(os.path.abspath(__file__))
# Check if .env is in backend/ or root
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)

image = (
    modal.Image.debian_slim()
    .pip_install(
        "psycopg2-binary", 
        "sqlalchemy",
        "intuit-oauth",
        "httpx",
        "rapidfuzz",
        "sqlmodel"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

app = modal.App("diag-tx")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
})

@app.function(image=image, secrets=[secrets])
async def diag_tx(realm_id: str, tx_id: str):
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")
        
    from app.db.session import SessionLocal
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            return "No connection found"
            
        client = QBOClient(db, connection)
        
        results = {}
        print(f"--- Diagnosing TX {tx_id} ---")
        
        for endpoint in ["Purchase", "Check", "BillPayment", "Deposit"]:
            try:
                res = await client.get_entity(endpoint, tx_id)
                results[endpoint] = res
                print(f"✅ Found in {endpoint}")
            except Exception as e:
                results[endpoint] = f"Error: {e}"
                print(f"❌ Not found in {endpoint}")
                
        return results
    finally:
        db.close()

@app.local_entrypoint()
async def main():
    realm_id = "9341456245321396"
    tx_id = "115"
    res = await diag_tx.remote.aio(realm_id, tx_id)
    import json
    print(json.dumps(res, indent=2))
