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
    print("🔍 Inspecting Specific Transaction ID 116...")
    
    db = SessionLocal()
    try:
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print("❌ No connection found")
            return

        client = QBOClient(db, conn)
        
        # Test Account-Scoped Query Visibility
        print(f"\n📡 Testing Account-Scoped Queries for Transfer ID 116...")
        
        # Try finding it via Venture X (Account 324)
        print("   👉 Querying by AccountRef = '324' (Venture X)...")
        # Note: Transfer has FromAccountRef and ToAccountRef. We should try both or generic AccountRef if supported.
        # But QBO Query language usually requires specific fields.
        
        queries = [
            "SELECT * FROM Transfer WHERE FromAccountRef = '324'",
            "SELECT * FROM Transfer WHERE ToAccountRef = '324'"
        ]
        
        for q in queries:
            print(f"   Running: {q}")
            try:
                res = await client.query(q)
                items = res.get("QueryResponse", {}).get("Transfer", [])
                found = False
                for item in items:
                    if item.get("Id") == "116":
                        print("✅ FOUND ID 116 via Account Scoped Query!")
                        found = True
                        break
                if not found:
                    print(f"   ❌ ID 116 not found in {len(items)} results.")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
