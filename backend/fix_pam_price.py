import modal
from dotenv import dotenv_values

app = modal.App("fix-pam-price")
env_vars = dotenv_values(".env")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "requests", "httpx", "pydantic-settings", "intuit-oauth")
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

@app.local_entrypoint()
def main():
    update_transaction.remote()

@app.function(image=image)
def update_transaction():
    from app.services.qbo_client import QBOClient
    from app.models.qbo import QBOConnection
    from app.models.user import User
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    import json
    import asyncio

    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        connection = db.query(QBOConnection).first()
        if not connection:
            print("No QBO Connection found.")
            return

        client = QBOClient(db, connection)
        
        target_id = "127"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run():
            # 1. Search for "Books by Bessie" in recent purchases
            print("Fetching recent purchases to scan for 'Books by Bessie'...")
            q_all = "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 100"
            r_all = await client.query(q_all)
            all_purchases = r_all.get("QueryResponse", {}).get("Purchase", [])
            
            print(f"Scanning {len(all_purchases)} recent purchases for Bessie...")
            for p in all_purchases:
                # check payeeref/entityref
                entity_name = p.get("EntityRef", {}).get("name", "")
                if "Bessie" in entity_name:
                    print(f"  - Found Bessie Transaction! ID: {p['Id']}, Amount: {p['TotalAmt']}, Date: {p['TxnDate']}")
                    if float(p.get("TotalAmt", 0)) == 75.0:
                        print(f"    Possible Duplicate! This matches the missing amount.")

            # 2. Fetch current transaction for Pam
            print(f"Fetching Purchase ID {target_id}...")
            # Use query or read endpoint? client.query is easier.
            q = f"SELECT * FROM Purchase WHERE Id = '{target_id}'"
            res = await client.query(q)
            purchases = res.get("QueryResponse", {}).get("Purchase", [])
            
            if not purchases:
                print(f"Transaction {target_id} not found!")
                return
            
            txn = purchases[0]
            print(f"Current Data: Amount={txn.get('TotalAmt')}, SyncToken={txn.get('SyncToken')}")
            
            # 3. Prepare Update
            # We must update TotalAmt AND the Line amount.
            new_amount = 75.00
            
            # Update Header
            txn['TotalAmt'] = new_amount
            
            # Update Lines
            lines = txn.get('Line', [])
            updated_lines = []
            for line in lines:
                # AccountBasedExpenseLineDetail usually holds the split
                if "AccountBasedExpenseLineDetail" in line:
                     line['Amount'] = new_amount 
                     # Ensure detail is preserved
                updated_lines.append(line)
            
            txn['Line'] = updated_lines
            
            # 4. Send Update
            print(f"Updating to Amount: {new_amount}...")
            
            try:
                # FIXED: use json_payload
                update_res = await client.request("POST", "purchase", json_payload=txn)
                # QBO returns dict, not response object? 
                # Wait, client.request returns res.json() (dict).
                # lines 73: return res.json()
                # So we can't check .status_code.
                # We check result dict directly.
                
                new_txn = update_res.get("Purchase")
                if new_txn:
                    print(f"Success! New Amount: {new_txn.get('TotalAmt')}, New SyncToken: {new_txn.get('SyncToken')}")
                else:
                    print(f"Update Result unexpected: {update_res}")
            except Exception as e:
                print(f"Request Error: {e}")

        loop.run_until_complete(run())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
