import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import dotenv_values

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# explicit env load
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")

if os.path.exists(env_path):
    print(f"✅ Found .env at {env_path}")
    env_vars = dotenv_values(env_path)
    print(f"🔑 Loaded {len(env_vars)} keys from .env")
    
    for key, val in env_vars.items():
        if val is not None:
             os.environ[key] = val
             
    if "FERNET_KEY" in os.environ:
         print(f"✅ FERNET_KEY is set in os.environ (Length: {len(os.environ['FERNET_KEY'])})")
    else:
         print("❌ FERNET_KEY is NOT set in os.environ")
else:
    print(f"❌ .env NOT found at {env_path}")

# Import AFTER env vars are set
from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount, Transaction
from app.models.user import User # Required for FK
from app.services.qbo_client import QBOClient

async def debug_venture_x():
    db = SessionLocal()
    try:
        # 0. Check GLOBAL Transaction Count
        print("\n🌍 Global Transaction Stats:")
        from sqlalchemy import func
        stats = db.query(Transaction.realm_id, func.count(Transaction.id)).group_by(Transaction.realm_id).all()
        
        total_global = 0
        for r_id, count in stats:
            print(f"  - Realm: {r_id} | Count: {count}")
            total_global += count
            
        print(f"  -> Total Transactions in DB: {total_global}")

        print("\n👥 Listing Users and Connections in DB:")
        users = db.query(User).all()
        target_conn = None
        
        for u in users:
            conns = db.query(QBOConnection).filter(QBOConnection.user_id == u.id).all()
            for c in conns:
                tx_count = db.query(Transaction).filter(Transaction.realm_id == c.realm_id).count()
                print(f"  User: {u.id} | Realm: {c.realm_id} | Txs in DB: {tx_count}")
                if tx_count > 0:
                    target_conn = c
        
        # 1. Use the connection with data, OR one that matches the largest transaction pool
        if not target_conn and len(stats) > 0:
             # Try to find a connection for the realm with data
             top_realm = stats[0][0]
             print(f"\n⚠️ Found data for Realm {top_realm} but no user connection matched initially?")
             # Try to find user for this realm
             conn = db.query(QBOConnection).filter(QBOConnection.realm_id == top_realm).first()
             if conn:
                 print(f"  -> Found connection for {top_realm}. Switching to it.")
                 target_conn = conn

        if target_conn:
             conn = target_conn
             print(f"\n👉 Auto-selected Realm with data: {conn.realm_id}")
        else:
             conn = db.query(QBOConnection).first()
             if conn:
                 print(f"\n👉 Using first Realm (No data found?): {conn.realm_id}")
             else:
                 print("❌ No connections found in DB.")
                 return


        # 2. Check Bank Accounts
        accounts = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id).all()
        print("\n🏦 Bank Accounts in DB:")
        active_ids = []
        venture_x_account = None
        for acc in accounts:
            status = "✅ Active" if acc.is_active else "❌ Inactive"
            print(f" - [{acc.id}] {acc.name} ({acc.currency}): {status}")
            if acc.is_active:
                active_ids.append(acc.id)
            if "Venture" in acc.name or "Savor" in acc.name: 
                venture_x_account = acc

        # 3. Activate Venture X if inactive
        if venture_x_account and not venture_x_account.is_active:
            print(f"\n⚠️ Activating Venture X Account [{venture_x_account.id}]...")
            venture_x_account.is_active = True
            db.commit()
            active_ids.append(venture_x_account.id)
            print("✅ Account Activated.")

        # 4. Count Transactions in DB and QBO
        client = QBOClient(db, conn)
        
        # Check specific QBO Entity Types (Counts)
        entity_types = ["Purchase", "JournalEntry", "Deposit", "Transfer", "CreditCardCredit", "Payment", "BillPayment"]
        
        print("\n📊 Checking Transaction Counts (No Date Filter):")
        
        for entity in entity_types:
             try:
                # QBO Count
                q_query = f"SELECT count(*) FROM {entity}"
                res = await client.query(q_query)
                q_count = res.get("QueryResponse", {}).get("totalCount", 0)
                
                # DB Count (Approximate mapping)
                # This is tricky because DB stores mixed types. Just showing QBO for now.
                print(f" - QBO {entity}: {q_count}")
                
             except Exception as e:
                print(f" - QBO {entity}: ❌ Error {e}")

        # Check Local DB Total
        total_db = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
        print(f"\n📚 Local DB Total Transactions: {total_db}")
        
        # Check Local DB for Venture X specifically
        if venture_x_account:
             vx_count = db.query(Transaction).filter(
                 Transaction.realm_id == conn.realm_id, 
                 Transaction.account_id == venture_x_account.id
             ).count()
             print(f"📚 Local DB Venture X Transactions: {vx_count}")





    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_venture_x())
