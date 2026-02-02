import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def investigate():
    db = SessionLocal()
    # Get the most recent connection
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    
    if not connection:
        print("No connections found in local DB.")
        return

    print(f"Investigating realm: {connection.realm_id}")
    
    # List known active/available accounts in DB
    db_accounts = db.query(BankAccount).filter(BankAccount.realm_id == connection.realm_id).all()
    print(f"\nDB Accounts for this realm ({len(db_accounts)}):")
    for a in db_accounts:
        print(f"- ID: '{a.id}', Name: '{a.name}'")

    qbo = QBOClient(db, connection)
    
    print("\nQuerying ALL Purchases (up to 1000)...")
    try:
        data = qbo.query("SELECT * FROM Purchase MAXRESULTS 1000")
        purchases = data.get("QueryResponse", {}).get("Purchase", [])
        print(f"Total Purchases and Expenses found: {len(purchases)}")
        
        account_stats = {}
        for p in purchases:
            acc_ref = p.get("AccountRef", {})
            acc_id = acc_ref.get("value")
            acc_name = acc_ref.get("name")
            key = f"ID: '{acc_id}' (Name: '{acc_name}')"
            account_stats[key] = account_stats.get(key, 0) + 1
            
        print("\nPurchases by Source Account:")
        if not account_stats:
            print("- No purchases found.")
        for acc, count in account_stats.items():
            print(f"- {acc}: {count} transactions")

        # Check for CreditCardCredit
        print("\nQuerying ALL CreditCardCredit...")
        data_cc = qbo.query("SELECT * FROM CreditCardCredit MAXRESULTS 1000")
        cc_objs = data_cc.get("QueryResponse", {}).get("CreditCardCredit", [])
        print(f"Total CreditCardCredits found: {len(cc_objs)}")

    except Exception as e:
        print(f"Error during query: {e}")

if __name__ == "__main__":
    investigate()
