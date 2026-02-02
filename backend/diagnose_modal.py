import modal
import os
from sqlalchemy import text
from dotenv import dotenv_values

# 1. Capture keys from local .env
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
env_vars = dotenv_values(env_path)

stub = modal.App("qbo-diagnostic")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi", 
        "psycopg2-binary", 
        "python-dotenv", 
        "sqlalchemy",
        "intuit-oauth",
        "requests",
        "pydantic-settings"
    )
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

secrets = modal.Secret.from_dict({
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
})

@stub.function(image=image, secrets=[secrets])
def check_schema_and_sync():
    # Import inside function to run on remote
    from app.db.session import SessionLocal
    from sqlalchemy import text
    
    print("🚀 Starting Diagnostic...")
    
    db = SessionLocal()
    try:
        # Get Realm ID
        print("\nFinding Realm ID...")
        res = db.execute(text("SELECT realm_id FROM bank_accounts LIMIT 1"))
        realm_id = res.scalar()
        print(f"Realm ID: {realm_id}")
        
        if not realm_id:
            print("❌ No realm found in DB? checking QBOConnection...")
            res = db.execute(text("SELECT realm_id FROM qbo_connections LIMIT 1"))
            realm_id = res.scalar()
            print(f"Connection Realm ID: {realm_id}")

        if realm_id:
            from app.models.qbo import QBOConnection
            from app.services.transaction_service import TransactionService
            
            conn = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
            if conn:
                print(f"Connection found for user {conn.user_id}")
                service = TransactionService(db, conn)
                print("🔄 Attempting sync_bank_accounts()...")
                try:
                    service.sync_bank_accounts()
                    print("✅ Sync Success!")
                except Exception as ex:
                    print(f"❌ Sync Failed with error: {ex}")
                    import traceback
                    traceback.print_exc()
            else:
                 print("❌ No QBOConnection object found via ORM")
        
        # Check Final Accounts
        print("\nFinal Accounts in DB:")
        result = db.execute(text(f"SELECT id, name, is_connected FROM bank_accounts WHERE realm_id = '{realm_id}'"))
        for row in result:
             print(f" - {row}")

    except Exception as e:
        print(f"❌ General Error: {e}")
    finally:
        db.close()
