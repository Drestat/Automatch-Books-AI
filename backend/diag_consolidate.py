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

app = modal.App("diag-consolidation")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://neondb_owner:npg_kETgK4j8fUNM@ep-broad-wildflower-ahi897rz-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require",
    "QBO_CLIENT_ID": "AB3FputY62ogSyTRHyKFfAuoYPTHgdhhWZWAUcwZaoCP8jg4jy",
    "QBO_CLIENT_SECRET": "A3ReIYsA4IWquJiIaatvh4OKHpcGo311YmuCrkHQ",
    "QBO_REDIRECT_URI": "https://ifvckinglovef1--qbo-sync-engine-fastapi-app.modal.run/api/v1/qbo/callback",
})

@app.function(image=image, secrets=[secrets])
async def test_consolidation(realm_id: str):
    import sys
    sys.path.append("/root")
    from app.db.session import SessionLocal
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, connection)
        
        # Query ALL Purchase
        res_p = await client.query("SELECT * FROM Purchase MAXRESULTS 100")
        purchases = res_p.get("QueryResponse", {}).get("Purchase", [])
        
        types = {}
        for p in purchases:
            pt = p.get("PaymentType")
            types[pt] = types.get(pt, 0) + 1
            
        # Query ALL Check
        res_c = await client.query("SELECT * FROM Check MAXRESULTS 100")
        checks = res_c.get("QueryResponse", {}).get("Check", [])
        
        return {
            "purchase_payment_types": types,
            "check_count": len(checks),
            "check_ids": [c["Id"] for c in checks][:10],
            "purchase_ids_with_check_type": [p["Id"] for p in purchases if p.get("PaymentType") == "Check"][:10]
        }
    finally:
        db.close()

@app.local_entrypoint()
async def main():
    res = await test_consolidation.remote.aio("9341456245321396")
    import json
    print(json.dumps(res, indent=2))
