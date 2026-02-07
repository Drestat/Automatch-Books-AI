import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection, BankAccount
from sqlalchemy import func

def check_accounts_and_tx_mapping():
    db = SessionLocal()
    try:
        # Get a Realm ID
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
        
        realm_id = conn.realm_id
        print(f"Checking Realm: {realm_id}")

        # Check Accounts
        accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).all()
        print(f"Total Accounts: {len(accounts)}")
        
        active_accounts = []
        for acc in accounts:
            print(f"Account: {acc.name} (ID: {acc.id}) | Active: {acc.is_active}")
            if acc.is_active:
                active_accounts.append(acc.id)

        print(f"Active Account IDs: {active_accounts}")

        # Check Transactions per Account
        tx_counts = db.query(
            Transaction.account_id, func.count(Transaction.id)
        ).filter(
            Transaction.realm_id == realm_id
        ).group_by(Transaction.account_id).all()

        print("--- Transactions by Account ID ---")
        for acc_id, count in tx_counts:
            is_active = acc_id in active_accounts
            print(f"Account ID: {acc_id} | Count: {count} | Is Active Target: {is_active}")

    finally:
        db.close()

if __name__ == "__main__":
    check_accounts_and_tx_mapping()
