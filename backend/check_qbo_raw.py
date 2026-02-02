"""
Direct check: What do the 15 Mastercard transactions actually look like in QBO?
"""
import modal
import os
from dotenv import dotenv_values
from modal import Image
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

image = Image.debian_slim(python_version="3.9").pip_install(
    "requests",
    "intuit-oauth",
    "python-dotenv",
    "pydantic-settings",
    "sqlalchemy",
    "psycopg2-binary"
).add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")

app = modal.App("check-qbo-data")

secrets = modal.Secret.from_dict({
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def check_mastercard_data():
    """Check what QBO actually returns for Mastercard"""
    from app.db.session import get_db
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = next(get_db())
    try:
        connection = db.query(QBOConnection).first()
        client = QBOClient(db, connection)
        
        # Get Mastercard purchases
        res = client.query("SELECT * FROM Purchase WHERE AccountRef = '41'")
        purchases = res.get("QueryResponse", {}).get("Purchase", [])
        
        print(f"\n{'='*120}")
        print(f"RAW QBO DATA FOR MASTERCARD (Account ID 41)")
        print(f"Total Purchases: {len(purchases)}")
        print(f"{'='*120}\n")
        
        for p in purchases:
            print(f"\n{'─'*120}")
            print(f"ID: {p.get('Id')} | Date: {p.get('TxnDate')} | Amount: ${p.get('TotalAmt')}")
            print(f"{'─'*120}")
            print(f"EntityRef (Payee): {p.get('EntityRef')}")
            print(f"PrivateNote: {p.get('PrivateNote')}")
            print(f"DocNumber: {p.get('DocNumber')}")
            print(f"CreateTime: {p.get('MetaData', {}).get('CreateTime')}")
            print(f"Has Line: {'Line' in p}")
            if "Line" in p:
                for i, line in enumerate(p["Line"]):
                    print(f"  Line {i}: LinkedTxn={line.get('LinkedTxn', [])}")
        
        print(f"\n{'='*120}\n")
        
    finally:
        db.close()
