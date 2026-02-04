import os
import sys
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import BankAccount

def enable_checking():
    db = SessionLocal()
    try:
        print("Enabling 'Checking' account (ID 35)...")
        acc = db.query(BankAccount).filter(BankAccount.id == "35").first()
        if acc:
            acc.is_active = True
            db.commit()
            print("✅ 'Checking' is now ACTIVE.")
        else:
            print("❌ Checking account not found.")

    finally:
        db.close()

if __name__ == "__main__":
    enable_checking()
