
import asyncio
import os
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.qbo_client import QBOClient
from dotenv import load_dotenv

load_dotenv()

async def check_active(realm_id):
    db = SessionLocal()
    try:
        connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
        client = QBOClient(db, connection)
        
        # Check Account 35
        print("🔍 Checking Account 35...")
        try:
            res35 = await client.request("GET", "account/35")
            print(f"Account 35 Active: {res35.get('Account', {}).get('Active')}")
        except Exception as e:
            print(f"❌ Error Account 35: {e}")

        # Check Account 71
        print("🔍 Checking Account 71...")
        try:
            res71 = await client.request("GET", "account/71")
            print(f"Account 71 Active: {res71.get('Account', {}).get('Active')}")
        except Exception as e:
            print(f"❌ Error Account 71: {e}")
            
        # Check Vendor 52
        print("🔍 Checking Vendor 52...")
        try:
            res52 = await client.request("GET", "vendor/52")
            print(f"Vendor 52 Active: {res52.get('Vendor', {}).get('Active')}")
        except Exception as e:
            print(f"❌ Error Vendor 52: {e}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_active('9341456245321396'))
