import modal
from dotenv import dotenv_values
import time

app = modal.App("monitor-pam-status")
env_vars = dotenv_values(".env")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "requests", "httpx", "pydantic-settings", "intuit-oauth")
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

@app.local_entrypoint()
def main():
    monitor_loop.remote()

@app.function(image=image)
def monitor_loop():
    from app.services.qbo_client import QBOClient
    from app.models.qbo import QBOConnection
    from app.models.user import User
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    import asyncio

    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    target_id = "127"
    
    try:
        connection = db.query(QBOConnection).first()
        if not connection:
            print("No QBO Connection found.")
            return

        client = QBOClient(db, connection)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print(f"📡 Monitoring Pam Seitz (ID {target_id}) in QBO...")
        print("Waiting for changes (SyncToken increase, etc.)...")
        
        last_sync_token = None
        
        async def check():
            nonlocal last_sync_token
            # Fetch
            q = f"SELECT * FROM Purchase WHERE Id = '{target_id}'"
            res = await client.query(q)
            purchases = res.get("QueryResponse", {}).get("Purchase", [])
            
            if not purchases:
                print("Transaction 127 not found!")
                return
            
            p = purchases[0]
            curr_sync = p.get("SyncToken")
            curr_amt = p.get("TotalAmt")
            curr_memo = p.get("PrivateNote", "")
            
            # Print status
            if last_sync_token is None:
                print(f"Initial State -> SyncToken: {curr_sync}, Amount: {curr_amt}, Memo: {curr_memo}")
                last_sync_token = curr_sync
            elif curr_sync != last_sync_token:
                print(f"🔔 CHANGE DETECTED! SyncToken: {last_sync_token} -> {curr_sync}")
                print(f"   New Amount: {curr_amt}")
                print(f"   New Memo: {curr_memo}")
                # Check line items for category
                for line in p.get("Line", []):
                     detail = line.get("AccountBasedExpenseLineDetail", {})
                     acc = detail.get("AccountRef", {})
                     print(f"   Category: {acc.get('name')} (Id: {acc.get('value')})")
                last_sync_token = curr_sync
            else:
                # No change
                pass

        # Loop for 60 seconds? Or until user stops? 
        # Modal function has timeout. I'll run for 2 minutes.
        end_time = time.time() + 120
        while time.time() < end_time:
             loop.run_until_complete(check())
             time.sleep(2)
        
        print("Monitoring ended.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
