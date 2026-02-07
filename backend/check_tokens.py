import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.models.qbo import QBOConnection

def check_tokens():
    db = SessionLocal()
    try:
        # Get a Realm ID
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
        
        user = db.query(User).filter(User.id == conn.user_id).first()
        if not user:
            print("No user found")
            return

        print(f"User ID: {user.id}")
        print(f"Token Balance: {user.token_balance}")
        print(f"Subscription Status: {user.subscription_status}")
        
        # Refill
        print("Refilling tokens to 1000...")
        user.token_balance = 1000
        user.monthly_token_allowance = 1000 # ensure allowance matches too if needed
        db.add(user)
        db.commit()
        print("Refill complete.")

    finally:
        db.close()

if __name__ == "__main__":
    check_tokens()
