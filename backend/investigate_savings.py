import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def investigate_savings():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    if not connection: 
        print("No connection found.")
        return

    qbo = QBOClient(db, connection)
    savings_id = "36" # From previous investigation output

    print(f"Targeting Savings Account ID: {savings_id}")
    
    # Try broader search across more entities
    entities = ["Purchase", "Deposit", "JournalEntry", "Transfer", "BillPayment", "Payment"]
    
    for entity in entities:
        try:
            # Query and check if any transaction references the savings account
            data = qbo.query(f"SELECT * FROM {entity} MAXRESULTS 100")
            txs = data.get("QueryResponse", {}).get(entity, [])
            
            found_count = 0
            for p in txs:
                # Check multiple ref fields
                p_str = str(p)
                if f"'value': '{savings_id}'" in p_str:
                    found_count += 1
            
            print(f"Entity: {entity} | Total checked: {len(txs)} | Linked to Savings: {found_count}")
            
            if found_count > 0:
                # Print one sample to see the structure
                for p in txs:
                    if f"'value': '{savings_id}'" in str(p):
                        print(f"SAMPLE {entity} structure:")
                        import pprint
                        pprint.pprint(p)
                        break
        except Exception as e:
            print(f"Entity: {entity} | Error: {e}")

if __name__ == "__main__":
    investigate_savings()
