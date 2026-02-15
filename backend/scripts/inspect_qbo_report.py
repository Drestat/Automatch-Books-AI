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
from app.models.user import User
from app.services.qbo_client import QBOClient

async def main():
    print("📊 Fetching QBO TransactionList Report...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print("❌ No connection found")
            return

        client = QBOClient(db, conn)
        
        # Fetch Report for Jan 24 - Jan 28
        start_date = "2026-01-24"
        end_date = "2026-01-28"
        
        endpoint = "reports/TransactionList"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "columns": "tx_date,txn_type,doc_num,name,memo,amount,account_name"
        }
        
        print(f"📡 Requesting Report: {endpoint} with params {params}")
        
        res = await client.request("GET", endpoint, params=params)
        
        rows = res.get("Rows", {}).get("Row", [])
        print(f"✅ Report Returned {len(rows)} Rows")
        
        for row in rows:
            # Report rows are complex: {"ColData": [{"value": "date"}, ...]}
            if "ColData" in row:
                cols = [c.get("value") for c in row["ColData"]]
                # Check for our amount
                row_str = str(cols)
                # Print everything for deep inspection if it matches remotely
                if "6046.26" in row_str or "6,046.26" in row_str or "CAPITAL" in str(cols).upper():
                     print(f"🎯 FOUND MATCH IN REPORT!")
                     print(f"   Raw: {cols}")
                     print(f"   Row Metadata: {row}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
