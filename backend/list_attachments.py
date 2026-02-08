import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.qbo_client import QBOClient

async def list_attachments():
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == "104").first()
    if not tx:
        print("Transaction 104 not found")
        return
        
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
    client = QBOClient(db, connection)
    
    # Query for all Attachables linked to this transaction
    query = f"SELECT * FROM Attachable WHERE AttachableRef.EntityRef.Type = 'BillPayment' AND AttachableRef.EntityRef.Value = '104'"
    print(f"Running query: {query}")
    try:
        res = await client.query(query)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Failed to query Attachables: {e}")

    # Also try querying all Attachables just to see what's there
    query_all = "SELECT * FROM Attachable ORDER BY MetaData.CreateTime DESC MAXRESULTS 5"
    print(f"\nRunning query: {query_all}")
    try:
        res = await client.query(query_all)
        attachables = res.get("QueryResponse", {}).get("Attachable", [])
        if attachables:
            print(f"Latest 5 Attachables:")
            for a in attachables:
                print(f"  Id: {a.get('Id')}, FileName: {a.get('FileName')}, CreateTime: {a.get('MetaData', {}).get('CreateTime')}")
                if a.get("AttachableRef"):
                    ref = a.get("AttachableRef")[0].get("EntityRef", {})
                    print(f"    Linked to: {ref.get('type')} {ref.get('value')}")
        else:
            print("No attachables found.")
    except Exception as e:
        print(f"Failed to query all Attachables: {e}")

if __name__ == "__main__":
    asyncio.run(list_attachments())
