import os
import sys
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.qbo import BankAccount

def diag_accounts():
    db = SessionLocal()
    try:
        print("Listing all Bank Accounts in DB:")
        print(f"{'ID':<10} | {'Name':<30} | {'Active?':<10} | {'Connected?':<10} | {'Balance'}")
        print("-" * 80)
        
        accounts = db.query(BankAccount).all()
        if not accounts:
            print("No accounts found.")
        
        for acc in accounts:
            print(f"{acc.id:<10} | {acc.name:<30} | {str(acc.is_active):<10} | {str(acc.is_connected):<10} | {acc.balance}")

    finally:
        db.close()

if __name__ == "__main__":
    diag_accounts()
