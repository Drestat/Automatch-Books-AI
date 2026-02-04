
import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path to import app modules
sys.path.append('/Users/andresmunoz2026/Library/Mobile Documents/com~apple~CloudDocs/2026 Projects/Antigravity/Quickbooks Bank Transactions 2/backend')

from app.db.session import SessionLocal
from app.models.qbo import Transaction, BankAccount

def diagnose_mastercard():
    db = SessionLocal()
    try:
        # Find Mastercard account
        mastercard = db.query(BankAccount).filter(BankAccount.name.ilike('%Mastercard%')).first()
        if not mastercard:
            print("❌ No 'Mastercard' account found.")
            # List all accounts
            accounts = db.query(BankAccount).all()
            print("Available accounts:")
            for a in accounts:
                print(f"- {a.name} (ID: {a.id})")
            return

        print(f"✅ Found Mastercard: {mastercard.name} (ID: {mastercard.id})")
        
        # Get 5 transactions from this account
        txs = db.query(Transaction).filter(
            Transaction.account_id == mastercard.id,
            Transaction.is_excluded == False
        ).limit(5).all()
        
        if not txs:
            print("❌ No transactions found for this account.")
            return

        print(f"🔍 Analyzing {len(txs)} transactions...")
        
        from app.core.feed_logic import FeedLogic
        
        for tx in txs:
            print(f"\n--------------------------------------------------")
            print(f"ID: {tx.id}")
            print(f"Desc: {tx.description}")
            print(f"Amount: {tx.amount}")
            print(f"Current Status: {tx.status}")
            print(f"Is QBO Matched (DB): {tx.is_qbo_matched}")
            
            raw = tx.raw_json
            if not raw:
                print("⚠️ No Raw JSON")
                continue
                
            # Run Logic
            is_matched, reason = FeedLogic.analyze(raw)
            print(f"FeedLogic Result: matched={is_matched}, reason='{reason}'")
            
            # Inspect Key Fields
            print(f"TxnType: {FeedLogic._get_txn_type(raw)}")
            print(f"ClrStatus: {FeedLogic._get_clr_status(raw)}")
            print(f"Has LinkedTxn: {FeedLogic._has_linked_txn(raw)}")
            print(f"Has Specific Cat: {FeedLogic._has_specific_category(raw)}")
            print(f"Has Payee: {FeedLogic._has_payee(raw)}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_mastercard()
