import modal
import os
from dotenv import dotenv_values
from app.db.session import SessionLocal
from app.models.qbo import Transaction, SyncLog
from sqlalchemy import inspect

# 1. Load Local Env Vars (Simulating Production Config)
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(base_dir), ".env")
env_vars = dotenv_values(env_path)

# 2. Define Secrets explicitly
secrets = modal.Secret.from_dict({
    "POSTGRES_USER": env_vars.get("POSTGRES_USER", ""),
    "POSTGRES_PASSWORD": env_vars.get("POSTGRES_PASSWORD", ""),
    "POSTGRES_HOST": env_vars.get("POSTGRES_HOST", ""),
    "POSTGRES_DB": env_vars.get("POSTGRES_DB", ""),
    "DATABASE_URL": env_vars.get("DATABASE_URL", ""),
    "GEMINI_API_KEY": env_vars.get("GEMINI_API_KEY", ""),
    "GEMINI_MODEL": env_vars.get("GEMINI_MODEL", "gemini-1.5-flash"), 
})

# 3. Define Standalone App
app = modal.App("debug-cloud-script")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "fastapi", "pydantic-settings", "python-dotenv", "rapidfuzz", "google-generativeai")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
)

@app.function(image=image, secrets=[secrets])
def debug_live_state():
    print("🕵️‍♂️ [Debug Cloud] Starting inspection...")
    # Add /root to path
    import sys
    sys.path.append("/root")

    try:
        from app.db.session import SessionLocal
        from app.models.qbo import Transaction, SyncLog
        
        db = SessionLocal()
        
        # 1. Check Schema Columns
        print("\n📊 Checking Table Schema for 'transactions'...")
        inspector = inspect(db.get_bind())
        columns = [c['name'] for c in inspector.get_columns('transactions')]
        
        required = ['vendor_reasoning', 'category_reasoning', 'tax_deduction_note']
        missing = [r for r in required if r not in columns]
        
        if missing:
            print(f"❌ CRITICAL: Missing columns in DB: {missing}")
            print("   Action required: Run alembic upgrade head")
        else:
            print(f"✅ Schema looks correct. Columns present: {required}")
            
        # 2. Check Recent Data
        print("\n🔍 Inspecting most recent 5 transactions...")
        recent_txs = db.query(Transaction).order_by(Transaction.date.desc()).limit(5).all()
        
        if not recent_txs:
             print("⚠️ No transactions found in DB.")
        
        for tx in recent_txs:
            print(f"   ID: {tx.id} | Desc: {tx.description}")
            print(f"   Reasoning (Old): {str(tx.reasoning)[:50] if tx.reasoning else 'None'}")
            print(f"   Vendor Reasoning: {tx.vendor_reasoning}")
            print(f"   Tax Note: {tx.tax_deduction_note}")
            print("   ---")
            
        # 3. Check All Transactions with Vendor Reasoning
        print("\n🧠 Transactions with AI Reasoning Populated:")
        # Check if vendor_reasoning is not null
        analyzed_txs = db.query(Transaction).filter(Transaction.vendor_reasoning != None).all()
        
        if not analyzed_txs:
            print("❌ NO transactions have vendor_reasoning occupied.")
        else:
            print(f"✅ Found {len(analyzed_txs)} analyzed transactions.")
            for tx in analyzed_txs:
                print(f"   🆔 {tx.id} | Desc: {tx.description}")
                print(f"      Vendor Reasoning: {str(tx.vendor_reasoning)[:50]}...")
                print(f"      Tax Note: {str(tx.tax_deduction_note)[:50]}...")
                print("   ---")
        
        db.close()

    except Exception as e:
        print(f"❌ Error inspecting DB: {e}")
        import traceback
        traceback.print_exc()

@app.local_entrypoint()
def main():
    debug_live_state.remote()
