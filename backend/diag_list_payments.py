
import asyncio
import os
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient
from dotenv import load_dotenv
import json

load_dotenv()

async def list_payments(realm_id):
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, connection)
        
        print(f"🔍 Fetching Payments...")
        res = await client.query("SELECT * FROM Payment MAXRESULTS 5")
        payments = res.get("QueryResponse", {}).get("Payment", [])
        
        if payments:
            print(f"Found {len(payments)} payments.")
            print(json.dumps(payments[0], indent=2))
        else:
            print("No payments found.")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(list_payments('9341456245321396'))
