import modal
import os

image = (
    modal.Image.debian_slim()
    .pip_install("psycopg2-binary", "sqlalchemy", "intuit-oauth", "httpx", "rapidfuzz", "sqlmodel")
    .add_local_dir(os.path.join(os.getcwd(), "app"), remote_path="/root/app")
)

app = modal.App("diag-queries")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://neondb_owner:npg_kETgK4j8fUNM@ep-broad-wildflower-ahi897rz-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require",
    "QBO_CLIENT_ID": "AB3FputY62ogSyTRHyKFfAuoYPTHgdhhWZWAUcwZaoCP8jg4jy",
    "QBO_CLIENT_SECRET": "A3ReIYsA4IWquJiIaatvh4OKHpcGo311YmuCrkHQ",
    "QBO_REDIRECT_URI": "https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run/api/v1/qbo/callback",
})

@app.function(image=image, secrets=[secrets])
async def check_queries(realm_id: str, tx_id: str):
    import sys
    sys.path.append("/root")
    from app.db.session import SessionLocal
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, connection)
        
        # Query Purchase
        res_p = await client.query(f"SELECT * FROM Purchase WHERE Id = '{tx_id}'")
        found_p = res_p.get("QueryResponse", {}).get("Purchase", [])
        
        # Query Check
        res_c = await client.query(f"SELECT * FROM Check WHERE Id = '{tx_id}'")
        found_c = res_c.get("QueryResponse", {}).get("Check", [])
        
        return {
            "in_purchase_query": len(found_p) > 0,
            "in_check_query": len(found_c) > 0
        }
    finally:
        db.close()

@app.local_entrypoint()
async def main():
    res = await check_queries.remote.aio("9341456245321396", "115")
    print(res)
