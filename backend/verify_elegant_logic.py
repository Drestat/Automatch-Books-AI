import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.qbo import Transaction, QBOConnection
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def verify_logic():
    print(f"Verifying Elegant Logic...")
    
    # 1. Fetch All Transactions (Simulating sync_all result)
    # Note: We need to make sure the DB actually HAS the transactions. 
    # If the user hasn't re-synced yet, the DB might be empty because we cleared it earlier.
    # But wait, the previous "Forensic" steps cleared the DB.
    # So right now the DB is EMPTY.
    
    txs = db.query(Transaction).all()
    print(f"Total Transactions in DB: {len(txs)}")
    
    if len(txs) == 0:
        print("⚠️ Database is empty! Cannot verify logic until Sync runs.")
        print("Next Step: Ask User to Trigger Sync via App.")
        return

    # 2. Apply Logic from get_transactions
    now_utc = datetime.now(timezone.utc)
    cutoff_date = now_utc - timedelta(days=90)
    print(f"Cutoff Date (90 days ago): {cutoff_date}")
    
    print("\n---------------------------------------------------")
    print(f"{'Description':<30} | {'Account':<25} | {'Date':<12} | {'Computed Status'}")
    print("---------------------------------------------------")
    
    for tx in txs:
        acc_name = (tx.account_name or "").lower()
        
        is_uncategorized_account = (
            "uncategorized" in acc_name 
            or "ask my accountant" in acc_name
            or not acc_name 
        )
        
        tx_date = tx.date
        if tx_date and tx_date.tzinfo is None:
            tx_date = tx_date.replace(tzinfo=timezone.utc)
            
        is_recent = tx_date >= cutoff_date
        
        status = "UNKNOWN"
        if is_uncategorized_account:
            status = "NEEDS_REVIEW"
        elif is_recent:
            status = "CATEGORIZED"
        else:
            status = "ARCHIVED"
            
        desc = (tx.description or "No Desc")[:28]
        date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
        
        print(f"{desc:<30} | {tx.account_name or 'None':<25} | {date_str:<12} | {status}")

    print("\n---------------------------------------------------")
    
if __name__ == "__main__":
    verify_logic()
