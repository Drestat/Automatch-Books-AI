import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.qbo_client import QBOClient

async def check_raw_qbo():
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == "104").first()
    if not tx:
        print("Transaction 104 not found")
        return
        
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    client = QBOClient(db, connection)
    
    # Try fetching it as BillPayment
    print(f"Fetching 104 as BillPayment...")
    try:
        res = await client.get_entity("104", "BillPayment")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Failed to fetch as BillPayment: {e}")
        
    # Try fetching it as Purchase (just in case)
    print(f"\nFetching 104 as Purchase...")
    try:
        res = await client.get_entity("104", "Purchase")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Failed to fetch as Purchase: {e}")

if __name__ == "__main__":
    asyncio.run(check_raw_qbo())
