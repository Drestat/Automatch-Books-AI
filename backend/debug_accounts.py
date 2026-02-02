import os
import sys
import json

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def debug_accounts():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    if not connection:
        print("No connection found.")
        return

    qbo = QBOClient(db, connection)
    
    # Get all accounts from DB
    db_accounts = db.query(BankAccount).filter(BankAccount.realm_id == connection.realm_id).all()
    print("DB Accounts:")
    for a in db_accounts:
        print(f"  ID: '{a.id}', Name: '{a.name}'")
    
    print("\n" + "="*80 + "\n")
    
    # Query all transaction types and show account references
    entities = ["Purchase", "Deposit", "Transfer"]
    
    for entity in entities:
        try:
            data = qbo.query(f"SELECT * FROM {entity} MAXRESULTS 50")
            txs = data.get("QueryResponse", {}).get(entity, [])
            
            print(f"\n{entity} Transactions ({len(txs)} found):")
            print("-" * 80)
            
            for tx in txs[:5]:  # Show first 5
                tx_id = tx.get("Id")
                tx_date = tx.get("TxnDate")
                
                # Extract all possible account references
                refs = []
                if "AccountRef" in tx:
                    refs.append(f"AccountRef: {tx['AccountRef'].get('value')} ({tx['AccountRef'].get('name')})")
                if "DepositToAccountRef" in tx:
                    refs.append(f"DepositToAccountRef: {tx['DepositToAccountRef'].get('value')} ({tx['DepositToAccountRef'].get('name')})")
                if "FromAccountRef" in tx:
                    refs.append(f"FromAccountRef: {tx['FromAccountRef'].get('value')} ({tx['FromAccountRef'].get('name')})")
                if "ToAccountRef" in tx:
                    refs.append(f"ToAccountRef: {tx['ToAccountRef'].get('value')} ({tx['ToAccountRef'].get('name')})")
                
                print(f"  TX {tx_id} ({tx_date}):")
                for ref in refs:
                    print(f"    {ref}")
                
                if not refs:
                    print(f"    NO ACCOUNT REFS FOUND - Keys: {list(tx.keys())}")
                    
        except Exception as e:
            print(f"{entity} Error: {e}")

if __name__ == "__main__":
    debug_accounts()
