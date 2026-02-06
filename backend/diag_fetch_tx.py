
import asyncio
import os
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient
from dotenv import load_dotenv

load_dotenv()

async def fetch_tx(realm_id, tx_id):
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, connection)
        
        print(f"🔍 Fetching Purchase {tx_id}...")
        try:
            res = await client.get_purchase(tx_id)
            print("--- FULL QBO RESPONSE ---")
            import json
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"❌ Error: {e}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(fetch_tx('9341456245321396', '84'))
