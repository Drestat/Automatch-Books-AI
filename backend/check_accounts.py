import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import BankAccount, Transaction

def check_accounts():
    db = SessionLocal()
    try:
        # Get active user from the god mode configuration step (user_39...)
        # We need the Realm ID associated with this user
        from app.models.user import User
        from app.models.qbo import QBOConnection
        
        user_id = "user_39ZWbRkFIGQwOHwSzNldksd7EY9"
        conn = db.query(QBOConnection).filter(QBOConnection.user_id == user_id).first()
        
        if not conn:
            print(f"❌ No connection found for user {user_id}")
            return

        print(f"🔍 Checking Accounts for Realm: {conn.realm_id}")
        
        accounts = db.query(BankAccount).filter(BankAccount.realm_id == conn.realm_id).all()
        print(f"Found {len(accounts)} accounts:")
        for a in accounts:
            tx_count = db.query(Transaction).filter(
                Transaction.realm_id == conn.realm_id,
                Transaction.account_id == a.id
            ).count()
            print(f"- [{a.name}] (ID: {a.id}) | Active: {a.is_active} | Connected: {a.is_connected} | Txs: {tx_count} | Balance: {a.balance}")

    finally:
        db.close()

if __name__ == "__main__":
    check_accounts()
