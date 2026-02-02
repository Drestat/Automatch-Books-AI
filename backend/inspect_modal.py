
import modal
import os
from dotenv import dotenv_values

# Reuse image definition logic
base_dir = os.path.dirname(os.path.abspath(__file__))
# Check if .env is in backend/ or root
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)

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
        "google-generativeai",
        "stripe",
        "rapidfuzz",
        "python-multipart",
        "pytz",
        "alembic"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
    .add_local_dir(os.path.join(base_dir, "alembic"), remote_path="/root/alembic")
    .add_local_file(os.path.join(base_dir, "alembic.ini"), remote_path="/root/alembic.ini")
)

app = modal.App("qbo-sync-engine-debug")

secrets = modal.Secret.from_dict({
    "POSTGRES_USER": env_vars.get("POSTGRES_USER", ""),
    "POSTGRES_PASSWORD": env_vars.get("POSTGRES_PASSWORD", ""),
    "POSTGRES_HOST": env_vars.get("POSTGRES_HOST", ""),
    "POSTGRES_DB": env_vars.get("POSTGRES_DB", ""),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
})

@app.function(image=image, secrets=[secrets])
def audit_mastercard_payees():
    """Check Payee status and CreateTime for all Mastercard items"""
    from app.services.qbo_client import QBOClient
    from app.db.session import get_db
    from app.models.qbo import QBOConnection
    
    db = next(get_db())
    try:
        connection = db.query(QBOConnection).first()
        client = QBOClient(db, connection)
        mid = "41"
        
        print("\n📊 MASTERCARD PAYEE AUDIT (ID 41)")
        print("="*120)
        
        entities = ["Purchase", "BillPayment", "CreditCardCredit"]
        for ent in entities:
            try:
                res = client.query(f"SELECT * FROM {ent}")
                items = res.get("QueryResponse", {}).get(ent, [])
                for it in items:
                    # Filter for Mastercard
                    is_hit = False
                    if ent == "Purchase" and it.get("AccountRef", {}).get("value") == mid: is_hit = True
                    elif ent == "BillPayment" and it.get("CreditCardPayment", {}).get("CCAccountRef", {}).get("value") == mid: is_hit = True
                    elif ent == "CreditCardCredit" and it.get("AccountRef", {}).get("value") == mid: is_hit = True
                    
                    if not is_hit: continue
                    
                    payee = it.get("EntityRef", {}).get("name", "--- NO PAYEE ---")
                    create_time = it.get("MetaData", {}).get("CreateTime", "N/A")
                    
                    print(f"ID: {it.get('Id'):<4} | {ent:<16} | Date: {it.get('TxnDate')} | Amt: {it.get('TotalAmt', 0.0):>8} | Payee: {payee:<25} | Created: {create_time}")
            except: pass
            
    finally:
        db.close()
