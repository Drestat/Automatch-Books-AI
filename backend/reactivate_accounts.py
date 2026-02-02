import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount

def reactivate_accounts():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connection found.")
        return
    
    realm_id = connection.realm_id
    print(f"Reactivating accounts for realm: {realm_id}\n")
    
    # Get all accounts
    accounts = db.query(BankAccount).filter(BankAccount.realm_id == realm_id).all()
    
    for acc in accounts:
        acc.is_active = True
        print(f"  Activated: {acc.name} (ID: {acc.id})")
    
    db.commit()
    print(f"\n✅ Reactivated {len(accounts)} accounts")

if __name__ == "__main__":
    reactivate_accounts()
