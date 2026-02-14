import os
import sys
from dotenv import dotenv_values
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
from app.models.qbo import Transaction, QBOConnection

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
    print("📊 Transaction Status Breakdown:")
    
    # 1. Get Realm ID
    conn = db.query(QBOConnection).first()
    if not conn:
        print("❌ No connection found")
        sys.exit(1)
        
    print(f"Realm: {conn.realm_id}")

    # 2. Group by Status and Account
    results = db.query(
        Transaction.account_id,
        Transaction.status, 
        Transaction.is_qbo_matched, 
        Transaction.is_excluded, 
        func.count(Transaction.id)
    ).filter(Transaction.realm_id == conn.realm_id).group_by(
        Transaction.account_id,
        Transaction.status, 
        Transaction.is_qbo_matched, 
        Transaction.is_excluded
    ).all()
    
    print(f"{'Account ID':<15} | {'Status':<25} | {'Matched':<8} | {'Excluded':<8} | {'Count':<5}")
    print("-" * 80)
    
    total = 0
    for r in results:
        acc_id, status, matched, excluded, count = r
        print(f"{str(acc_id):<15} | {str(status):<25} | {str(matched):<8} | {str(excluded):<8} | {count:<5}")
        total += count
        
    print("-" * 60)
    print(f"Total Transactions in DB: {total}")

finally:
    db.close()
