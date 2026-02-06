import modal
import os

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
        "alembic",
        "sqlmodel"
    )
    .add_local_dir(os.path.join(os.getcwd(), "app"), remote_path="/root/app")
)

app = modal.App("diag-tx-simple")

# Hardcoded secrets for diagnostic
secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://neondb_owner:npg_kETgK4j8fUNM@ep-broad-wildflower-ahi897rz-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require",
    "QBO_CLIENT_ID": "AB3FputY62ogSyTRHyKFfAuoYPTHgdhhWZWAUcwZaoCP8jg4jy",
    "QBO_CLIENT_SECRET": "A3ReIYsA4IWquJiIaatvh4OKHpcGo311YmuCrkHQ",
    "QBO_REDIRECT_URI": "https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run/api/v1/qbo/callback",
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
            return f"No connection found for realm {realm_id}"
            
        client = QBOClient(db, connection)
        
        results = {}
        print(f"--- Diagnosing TX {tx_id} ---")
        
        for endpoint in ["purchase", "check", "billpayment", "deposit"]:
            try:
                res = await client.request("GET", f"{endpoint}/{tx_id}")
                results[endpoint] = res
                print(f"✅ Found in {endpoint}")
            except Exception as e:
                # We want to see the actual error message from the request
                results[endpoint] = str(e)
                print(f"❌ Not found in {endpoint}: {e}")
                
        return results
    finally:
        db.close()

@app.local_entrypoint()
async def main():
    realm_id = "9341456245321396"
    tx_id = "115"
    try:
        res = await diag_tx.remote.aio(realm_id, tx_id)
        import json
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Failed: {e}")
