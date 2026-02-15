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
    print("🔍 Inspecting Account ID 296 (Capital One BC #1641)...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print("❌ No connection found")
            return

        client = QBOClient(db, conn)
        
        # Read Account Manually
        print(f"\n📡 Reading Account 296...")
        try:
            # Bypass get_entity which defaults to purchase
            res = await client.request("GET", "account/296")
            import json
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"❌ Failed to read Account 296: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
