import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount

def check_active_accounts():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    realm_id = connection.realm_id
    print(f"Checking realm: {realm_id}\n")
    
    # Get all accounts
    all_accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).all()
    print(f"Total accounts: {len(all_accounts)}")
    
    for acc in all_accounts:
        print(f"  ID: {acc.id}, Name: {acc.name}, Active: {acc.is_active}")
    
    # Get active accounts
    active_accounts = db.query(BankAccount).filter(
        BankAccount.realm_id == realm_id,
        BankAccount.is_active == True
    ).all()
    
    print(f"\nActive accounts: {len(active_accounts)}")
    if len(active_accounts) == 0:
        print("❌ NO ACTIVE ACCOUNTS! This is why sync didn't import anything.")
        print("The user needs to select accounts in the Account Selector Modal.")

if __name__ == "__main__":
    check_active_accounts()
