import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import QBOConnection, BankAccount
from app.services.qbo_client import QBOClient

def investigate():
    db = SessionLocal()
    connection = db.query(QBOConnection).order_by(QBOConnection.updated_at.desc()).first()
    if not connection: return

    qbo = QBOClient(db, connection)
    
    for entity in ["Purchase", "Deposit", "CreditCardCredit", "JournalEntry"]:
        try:
            data = qbo.query(f"SELECT * FROM {entity} MAXRESULTS 100")
            count = len(data.get("QueryResponse", {}).get(entity, []))
            print(f"Entity: {entity} | Count: {count}")
        except Exception as e:
            print(f"Entity: {entity} | Error: {e}")

if __name__ == "__main__":
    investigate()
