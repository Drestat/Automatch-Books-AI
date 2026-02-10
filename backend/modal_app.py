import modal
import os
from dotenv import dotenv_values

# 1. PRE-DEPLOY: Capture production keys from disk
base_dir = os.path.dirname(os.path.abspath(__file__))
# Check if .env is in backend/ or root
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)
print(f"🔍 [Modal Build] Env path: {env_path}")
print(f"🔍 [Modal Build] Keys found: {list(env_vars.keys())}")
print(f"🔍 [Modal Build] QBO_CLIENT_ID present: {bool(env_vars.get('QBO_CLIENT_ID'))}")

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
        "tenacity"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
    .add_local_dir(os.path.join(base_dir, "alembic"), remote_path="/root/alembic")
    .add_local_file(os.path.join(base_dir, "alembic.ini"), remote_path="/root/alembic.ini")
)

app = modal.App("qbo-sync-engine")
print("🔄 [Modal] forcing invalidation...")



# 3. SECRETS
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
    "GEMINI_MODEL": env_vars.get("GEMINI_MODEL", "gemini-1.5-flash"), # Fallback to stable 1.5 if missing
    "NEXT_PUBLIC_APP_URL": env_vars.get("NEXT_PUBLIC_APP_URL", ""),
})

@app.function(image=image, secrets=[secrets], min_containers=1, timeout=300)
@modal.asgi_app()
def fastapi_app():
    print("🚀 [Modal] ASGI Entrypoint waking up...")
    
    # Imports happen ONLY inside the cloud container
    import sys
    # Add /root to path so 'import app' works (app is at /root/app)
    if "/root" not in sys.path:
        sys.path.append("/root")
    
    try:
        from app.main import app as main_app
        from app.main import initialize_app_logic
        
        # Load the routers and models
        success = initialize_app_logic()
        
        if not success:
            print("⚠️ [Modal] Warning: App initialized with errors.")
            
        print("✅ [Modal] Ready to serve production traffic.")
        return main_app
    except Exception as e:
        error_msg = str(e)
        print(f"❌ [Modal] CRITICAL STARTUP ERROR: {error_msg}")
        # Return a fallback app so the container stays healthy but reports the error
        from fastapi import FastAPI
        err_app = FastAPI()
        @err_app.get("/{path:path}")
        def err(path: str):
            return {"error": "Startup Failed", "detail": error_msg}
        return err_app

@app.function(image=image, secrets=[secrets], timeout=600)
async def sync_user_data(realm_id: str):
    print(f"🔄 [Modal] Starting background sync for {realm_id}")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.services.sync_service import SyncService
    from app.models.qbo import QBOConnection
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("❌ Connection not found")
            return
            
        service = SyncService(db, connection)
        await service.sync_all()
        print("✅ Sync complete")
        
        # CHAIN TO AI
        print("🧠 Triggering Deterministic Analysis (Rules/History Only)...")
        # Disable AI for auto-sync to save tokens until user explicitly requests it
        process_ai_categorization.spawn(realm_id, allow_ai=False)
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    finally:
        db.close()

@app.function(image=image, secrets=[secrets], timeout=600)
def process_ai_categorization(realm_id: str, tx_id: str = None, allow_ai: bool = True):
    print(f"🧠 [Modal] Starting Analysis for {realm_id} (AI: {allow_ai})")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.db.session import SessionLocal
    from app.services.analysis_service import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db, realm_id)
        results = service.analyze_transactions(tx_id=tx_id, allow_ai=allow_ai)
        print(f"✅ Analysis complete. Processed {len(results)} transactions.")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    finally:
        db.close()

@app.function(image=image, secrets=[secrets], timeout=600)
async def bulk_approve_modal(realm_id: str, tx_ids: list[str]):
    print(f"🔄 [Modal] Starting Bulk Approve for {len(tx_ids)} transactions in {realm_id}")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.services.transaction_service import TransactionService
    from app.models.qbo import QBOConnection
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("❌ Connection not found")
            return
            
        service = TransactionService(db, connection)
        results = await service.bulk_approve(tx_ids)
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        print(f"✅ Bulk Approve Complete. Success: {success_count}/{len(tx_ids)}")
        
    except Exception as e:
        print(f"❌ Bulk Approve Failed: {e}")
    finally:
        db.close()

@app.function(image=image, secrets=[secrets], timeout=300)
def process_receipt_modal(realm_id: str, file_content: bytes, filename: str, mime_type: str = "image/jpeg"):
    """
    Process receipt image using Gemini Vision (Serverless)
    Returns extracted data and potential match ID.
    """
    print(f"🧾 [Modal] Processing receipt for {realm_id}: {filename} ({mime_type})")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.db.session import SessionLocal
    from app.services.receipt_service import ReceiptService
    
    db = SessionLocal()
    try:
        service = ReceiptService(db, realm_id)
        result = service.process_receipt(file_content, filename, mime_type=mime_type)
        
        # Unwrap SQLModel/ORM object to return serializable data
        match = result.get('match')
        return {
            "extracted": result.get('extracted'),
            "match_id": match.id if match else None
        }
    except Exception as e:
        print(f"❌ Receipt processing failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@app.function(image=image, secrets=[secrets], timeout=300)
async def process_single_approval(realm_id: str, tx_id: str):
    """
    Background worker to push a single optimistic approval to QBO.
    """
    print(f"🔄 [Modal] Syncing optimistic approval for {tx_id} in {realm_id}")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.services.transaction_service import TransactionService
    from app.models.qbo import QBOConnection
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        if not connection:
            print("❌ Connection not found")
            return
            
        service = TransactionService(db, connection)
        await service.sync_approved_to_qbo(tx_id)
        print(f"✅ Sync complete for {tx_id}")
        
    except Exception as e:
        print(f"❌ Sync failed for {tx_id}: {e}")
    finally:
        db.close()

@app.function(image=image, secrets=[secrets], timeout=600, schedule=modal.Cron("0 */6 * * *"))
async def auto_accept_worker():
    """
    Worker to auto-approve high-confidence matches for Founder/Empire tiers.
    """
    print("🤖 [Modal] Starting Auto-Accept Cron Job...")
    import sys
    if "/root" not in sys.path:
        sys.path.append("/root")

    from app.models.user import User
    from app.models.qbo import Transaction, QBOConnection
    from app.services.transaction_service import TransactionService
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        # 1. Target Premium Users who have Auto-Accept ENABLED
        premium_users = db.query(User).filter(
            User.subscription_tier.in_(['founder', 'empire']),
            User.auto_accept_enabled == True
        ).all()
        user_ids = [u.id for u in premium_users]
        
        if not user_ids:
            print("ℹ️ No premium users found for auto-accept.")
            return

        # 2. Find High Confidence Matches (>95%)
        # Note: We filter by realm_id associated with these users
        connections = db.query(QBOConnection).filter(QBOConnection.user_id.in_(user_ids)).all()
        
        for conn in connections:
            service = TransactionService(db, conn)
            
            # Find txs: unmatched, high confidence, not forced_review
            candidates = db.query(Transaction).filter(
                Transaction.realm_id == conn.realm_id,
                Transaction.status == 'unmatched',
                Transaction.confidence >= 0.95,
                Transaction.forced_review == False
            ).all()
            
            if not candidates:
                continue
                
            print(f"🚀 [Auto-Accept] Processing {len(candidates)} candidates for realm {conn.realm_id}")
            for tx in candidates:
                # Use synchronous-ish path here as we are already in a background worker
                try:
                    # We use approve_transaction(optimistic=False) to run it sequentially in this worker
                    await service.approve_transaction(tx.id, optimistic=False)
                except Exception as e:
                    print(f"⚠️ Failed auto-accept for {tx.id}: {e}")

        print("✅ Auto-Accept Cron Job complete.")
        
    except Exception as e:
        print(f"❌ Auto-Accept Job failed: {e}")
    finally:
        db.close()

@app.function(image=image, secrets=[secrets])
def daily_maintenance():
    print("Running daily maintenance tasks...")

@app.function(image=image, secrets=[secrets])
def run_migrations():
    import subprocess
    import os
    print("🏗️ [Modal] Running database migrations...")
    
    # Alembic needs to find the config relative to its execution
    # We set sqlalchemy.url dynamically if needed or rely on env vars in env.py
    try:
        # Check if DATABASE_URL is set
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
             print("❌ DATABASE_URL not set in environment.")
             return
             
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/root",
            capture_output=True,
            text=True
        )
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Migrations applied successfully.")
        else:
            print("❌ Migration failed.")
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")

    finally:
        engine.dispose()





