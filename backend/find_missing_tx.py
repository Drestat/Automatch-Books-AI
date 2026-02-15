import os
import sys
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.qbo import Transaction, QBOConnection
from datetime import datetime, timedelta
from sqlalchemy import func

# Load Env
env_path = ".env"
env_vars = dotenv_values(env_path)
for key, value in env_vars.items():
    os.environ[key] = value

# DB Setup
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("🔍 Searching for Transaction...")
    
    # 1. Get Realm ID
    conn = db.query(QBOConnection).first()
    if not conn:
        print("❌ No connection found")
        sys.exit(1)
        
    print(f"Realm: {conn.realm_id}")

    # 2. Check Date Range
    min_date, max_date = db.query(func.min(Transaction.date), func.max(Transaction.date)).filter(Transaction.realm_id == conn.realm_id).first()
    print(f"\n📅 DB Date Range for Realm {conn.realm_id}:")
    print(f" - Earliest: {min_date}")
    print(f" - Latest:   {max_date}")

    # 3. Search by Date 2026-01-26
    target_date_str = "2026-01-26"
    print(f"\n📅 Searching for transactions specifically on {target_date_str}:")
    
    date_obj = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    
    txs_date = db.query(Transaction).filter(
        Transaction.realm_id == conn.realm_id,
        Transaction.date >= date_obj,
        Transaction.date < date_obj + timedelta(days=1)
    ).all()
    
    if txs_date:
        for tx in txs_date:
            print(f" - ID: {tx.id} | Date: {tx.date} | Desc: {tx.description} | Amt: {tx.amount} | Type: {tx.transaction_type} | Acc: {tx.account_name}")
    else:
        print(f"❌ No transactions found on {target_date_str}")

finally:
    db.close()
