import os
import sys
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection
from app.services.token_service import TokenService

def add_tokens():
    db = SessionLocal()
    try:
        # Get the first connection/user
        conn = db.query(QBOConnection).first()
        if not conn:
            print("No connection found")
            return
            
        user_id = conn.user_id
        ts = TokenService(db)
        
        current = ts.get_balance(user_id)
        print(f"Current Balance: {current}")
        
        # Add 100 tokens manually
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.token_balance += 100
            db.add(user)
            db.commit()
            print(f"Added 100 tokens. New Balance: {user.token_balance}")
        else:
            print("User not found?")

    finally:
        db.close()

if __name__ == "__main__":
    add_tokens()
