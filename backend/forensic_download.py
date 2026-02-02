"""
Mastercard Forensic Audit: Download raw JSON for all 15 transactions
"""
import modal
import os
import json
from dotenv import dotenv_values
from modal import Image

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

app = modal.App("forensic-audit")

secrets = modal.Secret.from_dict({
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@app.function(image=image, secrets=[secrets])
def download_mastercard_json():
    """Download and dump all Mastercard purchase JSONs to a string for analysis"""
    from app.db.session import get_db
    from app.models.qbo import QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = next(get_db())
    try:
        connection = db.query(QBOConnection).first()
        client = QBOClient(db, connection)
        
        # Get all purchases and filter in Python to avoid query syntax issues
        res = client.query("SELECT * FROM Purchase")
        all_purchases = res.get("QueryResponse", {}).get("Purchase", [])
        
        # Account ID for Mastercard is 41
        purchases = [p for p in all_purchases if p.get("AccountRef", {}).get("value") == "41"]
        
        print(f"DEBUG: Found {len(purchases)} Mastercard purchases out of {len(all_purchases)} total")
        
        # We'll just return the JSON string to be printed in logs
        return json.dumps(purchases, indent=2)
        
    finally:
        db.close()

if __name__ == "__main__":
    with app.run():
        result = download_mastercard_json.remote()
        with open("mastercard_raw_forensics.json", "w") as f:
            f.write(result)
        print("Done! Data saved to mastercard_raw_forensics.json")
