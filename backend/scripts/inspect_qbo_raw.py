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
from app.models.user import User # IMPORTANT
from app.services.qbo_client import QBOClient

async def main():
    print("🔍 Inspecting Raw QBO Data for 2026-01-26...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print("❌ No connection found")
            return

        client = QBOClient(db, conn)
        
        entities = ["Purchase", "Deposit", "JournalEntry", "Transfer", "BillPayment", "Payment", "CreditCardPayment", "SalesReceipt", "CreditMemo", "CreditCardCredit", "RefundReceipt"]
        # Search a range around the date
        target_dates = ["2026-01-24", "2026-01-25", "2026-01-26", "2026-01-27"]
        
        print(f"💥 DUMPING EVERYTHING FOR DATES: {target_dates} 💥")
        
        for entity in entities:
             for target_date in target_dates:
                print(f"\n📡 Querying {entity} for {target_date}...")
                query = f"SELECT * FROM {entity} WHERE TxnDate = '{target_date}' MAXRESULTS 1000"
                try:
                    res = await client.query(query)
                    items = res.get("QueryResponse", {}).get(entity, [])
                    
                    if items:
                        print(f"✅ Found {len(items)} items in {entity} on {target_date}:")
                        for item in items:
                            # Print generic summary
                            amt = item.get("TotalAmt") or item.get("Amount")
                            desc = item.get("PrivateNote") or item.get("Description") or ""
                            # Check header description
                            if not desc and "Line" in item:
                                 for l in item["Line"]:
                                     desc += (l.get("Description") or "") + " "
                            
                            print(f"   👉 [{entity}] ID: {item.get('Id')} | Amt: {amt} | Ref: {item.get('DocNumber', 'N/A')} | Desc: {desc[:50]}...")
                            
                            # If it looks even remotely like our target, dump it full
                            if "6046" in str(amt) or "CAPITAL" in str(item).upper():
                                 print("      🔍 SUSPICIOUS ITEM DUMP:")
                                 import json
                                 print(json.dumps(item, indent=2))
                    else:
                        print(f"   (No items found)")
                except Exception as e:
                    print(f"   ❌ Error querying {entity}: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
