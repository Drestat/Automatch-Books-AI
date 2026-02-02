import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction, BankAccount

def check_db_transactions():
    db = SessionLocal()
    try:
        # Get all transactions
        all_txs = db.query(Transaction).all()
        print(f"📊 Total transactions in DB: {len(all_txs)}\n")
        
        # Group by account_id
        by_account = {}
        for tx in all_txs:
            acc_id = tx.account_id or "NULL"
            if acc_id not in by_account:
                by_account[acc_id] = []
            by_account[acc_id].append(tx)
        
        print("Transactions by account_id:")
        for acc_id, txs in sorted(by_account.items()):
            print(f"  Account {acc_id}: {len(txs)} transactions")
        
        print("\n" + "="*80)
        
        # Get all bank accounts
        accounts = db.query(BankAccount).all()
        print(f"\n📋 Bank Accounts in DB:")
        for acc in accounts:
            print(f"  ID: {acc.id} | Name: {acc.name} | Active: {acc.is_active} | Connected: {acc.is_connected}")
        
        print("\n" + "="*80)
        
        # Show sample transactions
        print("\n📝 Sample Transactions:")
        for tx in all_txs[:10]:
            print(f"ID: {tx.id} | Account: {tx.account_id} | Amount: ${tx.amount} | Date: {tx.date}")
            print(f"  Description: {tx.description}")
            print(f"  Matched: {tx.is_qbo_matched} | Status: {tx.status}")
            print()
        
    finally:
        db.close()

if __name__ == "__main__":
    check_db_transactions()
