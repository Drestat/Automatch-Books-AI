import modal
import sys
import os
import asyncio
from datetime import datetime
from dotenv import dotenv_values

# 1. Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
# Backend root is one level up from scripts/
backend_dir = os.path.dirname(current_dir)
env_path = os.path.join(backend_dir, ".env")

# 2. Load Env Vars
env_vars = dotenv_values(env_path)
print(f"🔍 [Script] Loaded env from {env_path}: {len(env_vars)} keys")

# 3. Define Image (Copy from modal_app.py)
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
        "tenacity",
        "cryptography"
    )
    .add_local_dir(os.path.join(backend_dir, "app"), remote_path="/root/app")
)

# 4. Define Secret
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
    "GEMINI_API_KEY": env_vars.get("GEMINI_API_KEY", ""),
    "GEMINI_MODEL": env_vars.get("GEMINI_MODEL", "gemini-1.5-flash"),
    "NEXT_PUBLIC_APP_URL": env_vars.get("NEXT_PUBLIC_APP_URL", ""),
    "FERNET_KEY": env_vars.get("FERNET_KEY", ""),
})

# 5. Define App
app = modal.App("qbo-force-sync-script")

@app.function(image=image, secrets=[secrets], timeout=600)
async def force_sync_remote():
    """
    Forces a sync for the specific user ID directly in the production environment.
    """
    import sys
    # Ensure /root is in path so 'from app...' works
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.db.session import SessionLocal
    from app.models.qbo import QBOConnection, Transaction, BankAccount
    from app.services.sync_service import SyncService
    
    print(f"🚀 [Remote] Starting Force Sync at {datetime.now()}")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print(f"❌ [Remote] No connection found for user {user_id}")
            return

        print(f"🔄 [Remote] Syncing Realm: {conn.realm_id}")
        
        # Check pre-sync count
        pre_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
        print(f"📊 [Remote] Pre-sync Tx Count: {pre_count}")
        
        # Inline Debug Sync Logic (to avoid modifying App code if possible, or just call service)
        # We will call service but monkey-patch or just rely on its print statements?
        # The service prints "Retrieved X raw items".
        
        # Let's verify active accounts first
        active_banks = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id, BankAccount.is_active == True).all()
        print(f"✅ [Remote] Active Accounts: {[f'{b.name} ({b.id})' for b in active_banks]}")
        
        service = SyncService(db, conn)
        await service.sync_transactions()
        
        # Check post-sync count
        post_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
        print(f"📊 [Remote] Post-sync Tx Count: {post_count}")
        print(f"✅ [Remote] Sync Complete. Added {post_count - pre_count} new transactions.")
        
    except Exception as e:
        print(f"❌ [Remote] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
