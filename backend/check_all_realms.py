import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection, BankAccount
from sqlalchemy import func

def check_all_data():
    db = SessionLocal()
    try:
        # Check all realms
        connections = db.query(QBOConnection).all()
        print(f"📊 QBO Connections: {len(connections)}\n")
        
        for conn in connections:
            print(f"Realm ID: {conn.realm_id}")
            print(f"User ID: {conn.user_id}")
            
            # Count transactions for this realm
            tx_count = db.query(Transaction).filter(Transaction.realm_id == conn.realm_id).count()
            print(f"Transactions: {tx_count}")
            
            # Count accounts
            acc_count = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id).count()
            active_count = db.query(BankAccount).filter(
                BankAccount.realm_id == conn.realm_id,
                BankAccount.is_active == True
            ).count()
            print(f"Accounts: {acc_count} (Active: {active_count})")
            print()
        
        # Check if there are ANY transactions at all
        total_txs = db.query(Transaction).count()
        print(f"\n🔍 Total transactions across ALL realms: {total_txs}\n")
        
        if total_txs > 0:
            # Show some samples
            print("Sample transactions:")
            samples = db.query(Transaction).limit(5).all()
            for tx in samples:
                print(f"  ID: {tx.id} | Realm: {tx.realm_id} | Account: {tx.account_id} | ${tx.amount}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_all_data()
