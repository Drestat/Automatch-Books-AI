import asyncio
import os
import sys
from dotenv import dotenv_values

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
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient

async def main():
    print("🔍 Searching ALL QBO Entities for '6046.26'...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print("❌ No connection found")
            return

        client = QBOClient(db, conn)
        
        entities = [
            "Purchase", "Deposit", "JournalEntry", "Transfer", 
            "BillPayment", "Payment", "CreditCardPayment", "SalesReceipt",
            "RefundReceipt", "CreditMemo", "Account"
        ]
        
        for entity in entities:
            print(f"\n📡 Querying {entity} (Latest 1000)...")
            # Fetch as many as possible (1000)
            query = f"SELECT * FROM {entity} ORDERBY TxnDate DESC MAXRESULTS 1000"
            try:
                res = await client.query(query)
                items = res.get("QueryResponse", {}).get(entity, [])
                
                found_any = False
                for item in items:
                    item_str = str(item)
                    if "6046.26" in item_str or "6046" in item_str:
                        found_any = True
                        print(f"✅ FOUND in {entity}!")
                        print(f"--- ID: {item.get('Id')} | Date: {item.get('TxnDate')} ---")
                        import json
                        print(json.dumps(item, indent=2))
                
                if not found_any:
                    # If it's a large table, we might need pagination, but for now let's hope it's in the first 1000
                    pass
            except Exception as e:
                print(f"   ❌ Error querying {entity}: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
