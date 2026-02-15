import asyncio
import os
import sys
from dotenv import dotenv_values
from datetime import datetime

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Load Env
env_path = os.path.join(backend_dir, ".env")
env_vars = dotenv_values(env_path)
for key, value in env_vars.items():
    os.environ[key] = value

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, Transaction
from app.services.qbo_client import QBOClient

async def main():
    print("🛠️ Applying Manual Fix for Missing Transaction 116...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        client = QBOClient(db, conn)
        
        # 1. Fetch from QBO via READ (which we know works)
        print("📡 Fetching Transfer/116 from QBO...")
        try:
            tx_data = await client.request("GET", "transfer/116")
            transfer = tx_data.get("Transfer")
            if not transfer:
                print("❌ Failed to fetch Transfer 116")
                return
                
            print(f"✅ Fetched Transfer 116. Amt: {transfer.get('Amount')}")
            
            # 2. Check if exists in DB
            existing = db.query(Transaction).filter(Transaction.id == "116").first()
            if existing:
                print(f"⚠️ Transaction 116 already exists in DB (ID: {existing.id}). Updating...")
                # Maybe it was linked to the wrong account?
            
            # 3. Prepare DB Object
            # We want to link it to Venture X (Account 324) because 296 is inactive
            target_account_id = "324" 
            
            tx_obj = existing or Transaction(id="116")
            
            tx_obj.user_id = user_id
            tx_obj.qbo_account_id = target_account_id
            # qbo_account_id is the foreign key to BankAccount. 
            # We previously determined 324 is the local ID for Venture X.
            # Make sure this matches the Local DB ID, not QBO ID.
            # My logic in sync_service uses `account_id` for the local ID.
            # Let's double check model.
            # Transaction.account_id -> ForeignKey('bank_accounts.id')
            tx_obj.account_id = int(target_account_id)
            
            tx_obj.amount = transfer.get("Amount")
            tx_obj.date = datetime.strptime(transfer.get("TxnDate"), "%Y-%m-%d").date()
            tx_obj.description = transfer.get("PrivateNote") or "Credit Card Payment (Transfer)"
            tx_obj.transaction_type = "Transfer"
            tx_obj.currency = transfer.get("CurrencyRef", {}).get("value", "USD")
            tx_obj.status = "posted"
            tx_obj.raw_json = transfer
            
            # 4. Save
            db.add(tx_obj)
            db.commit()
            db.refresh(tx_obj)
            print(f"✅ Transaction 116 saved to DB! Local ID: {tx_obj.id}")
            
        except Exception as e:
            print(f"❌ Error applying fix: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
