
import modal
import os

# Reuse the image and app definition logic from modal_app.py for consistency
base_dir = os.path.dirname(os.path.abspath(__file__))

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
        "pytz"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

app = modal.App("qbo-sync-engine-diag")

# Need to pull env vars for the secret
from dotenv import dotenv_values
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
    "QBO_CLIENT_ID": env_vars.get("QBO_CLIENT_ID", ""),
    "QBO_CLIENT_SECRET": env_vars.get("QBO_CLIENT_SECRET", ""),
    "QBO_REDIRECT_URI": env_vars.get("QBO_REDIRECT_URI", ""),
    "QBO_ENVIRONMENT": env_vars.get("QBO_ENVIRONMENT", "sandbox"),
})

@app.function(image=image, secrets=[secrets])
async def diagnose_tx_77_modal():
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")
        
    from app.db.session import SessionLocal
    from app.models.qbo import Transaction, QBOConnection
    from app.services.qbo_client import QBOClient
    
    db = SessionLocal()
    tx_id = "77"
    
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        print(f"Transaction {tx_id} not found in DB")
        return
        
    conn = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    client = QBOClient(db, conn)
    
    print(f"--- Diagnosing Transaction {tx.id} ---")
    
    # Check Account
    cat_id = tx.category_id or tx.suggested_category_id
    if cat_id:
        print(f"Checking Account {cat_id}...")
        try:
            acc = await client.request("GET", f"account/{cat_id}")
            print(f"✅ Account {cat_id} found: {acc.get('Account', {}).get('Name')} (Active: {acc.get('Account', {}).get('Active')})")
        except Exception as e:
            print(f"❌ Account {cat_id} NOT FOUND or Error: {e}")
            
    # Check Vendor
    payee_name = tx.payee or tx.suggested_payee
    if payee_name:
        print(f"Checking Vendor for '{payee_name}'...")
        try:
            vendor = await client.get_vendor_by_name(payee_name)
            if vendor:
                print(f"✅ Vendor found: {vendor.get('DisplayName')} (Id: {vendor.get('Id')}, Active: {vendor.get('Active')})")
            else:
                print(f"❌ Vendor '{payee_name}' NOT FOUND")
        except Exception as e:
            print(f"❌ Vendor check failed: {e}")

    # Check Transaction itself
    print(f"Checking Purchase {tx.id} in QBO...")
    try:
        qbo_tx = await client.get_purchase(tx.id)
        purchase = qbo_tx.get("Purchase", {})
        print(f"✅ Purchase {tx.id} found in QBO.")
        print(f"SyncToken: {purchase.get('SyncToken')}")
        for line in purchase.get('Line', []):
            if "LinkedTxn" in line:
                print(f"🔗 Found LinkedTxn: {line['LinkedTxn']}")
                for link in line['LinkedTxn']:
                    try:
                        lt_id = link['TxnId']
                        lt_type = link['TxnType']
                        print(f"  Checking Linked {lt_type} {lt_id}...")
                        lt_res = await client.request("GET", f"{lt_type.lower()}/{lt_id}")
                        print(f"  ✅ Linked {lt_type} {lt_id} found and active.")
                    except Exception as le:
                        print(f"  ❌ Linked {lt_type} {lt_id} NOT FOUND or Error: {le}")
    except Exception as e:
        print(f"❌ Purchase {tx.id} NOT FOUND in QBO: {e}")
    finally:
        db.close()
