import modal
from dotenv import dotenv_values

app = modal.App("query-qbo-checking")
env_vars = dotenv_values(".env")

image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "requests", "httpx", "pydantic-settings", "intuit-oauth")
    .env(env_vars)
    .add_local_dir("app", remote_path="/root/app")
)

@app.local_entrypoint()
def main():
    query_checking.remote()

@app.function(image=image)
def query_checking():
    from app.services.qbo_client import QBOClient
    from app.models.qbo import QBOConnection
    from app.models.user import User # Required for FK resolution
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
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
        
        # 1. Verify Account ID for "Checking"
        print("Finding Checking Account...")
        acc_query = "SELECT * FROM Account WHERE AccountType = 'Bank' MAXRESULTS 100"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run():
            res = await client.query(acc_query)
            accounts = res.get("QueryResponse", {}).get("Account", [])
            checking_id = None
            for acc in accounts:
                if "Checking" in acc["Name"]:
                    print(f"Found Account: {acc['Name']} (Id: {acc['Id']})")
                    checking_id = acc["Id"]
                    # Keep looking in case there are multiple, but pick last or first?
            
            if not checking_id:
                print("Could not find account with 'Checking' in name. Listing all banks:")
                for acc in accounts:
                    print(f" - {acc['Name']} (Id: {acc['Id']})")
                return

            print(f"Using Account ID: {checking_id} for deep search.")
            
            # 2. Query Purchases, Checks, JournalEntries (Fetch recent ~100 of each and filter locally)
            
            print("Fetching recent 'Purchase' transactions...")
            q1 = "SELECT * FROM Purchase ORDERBY TxnDate DESC MAXRESULTS 300"
            r1 = await client.query(q1)
            purchases = r1.get("QueryResponse", {}).get("Purchase", [])
            print(f"Fetched {len(purchases)} Purchases.")
            
            # Check is often covered by Purchase (PaymentType='Check')
            # But skipping explicit 'Check' query to avoid 400 error if entity is restricted.
            checks = []
            
            print("Fetching recent 'JournalEntry' transactions...")
            q3 = "SELECT * FROM JournalEntry MAXRESULTS 100"
            r3 = await client.query(q3)
            jes = r3.get("QueryResponse", {}).get("JournalEntry", [])
            print(f"Fetched {len(jes)} JournalEntries.")
            
            print("Fetching recent 'BillPayment' transactions...")
            q4 = "SELECT * FROM BillPayment ORDERBY TxnDate DESC MAXRESULTS 100"
            r4 = await client.query(q4)
            bps = r4.get("QueryResponse", {}).get("BillPayment", [])

            # Combine and search locally
            all_txs = purchases + checks + jes + bps
            print(f"Scanning {len(all_txs)} recent transactions for 'Pam' or 'Seitz'...")
            
            found_count = 0
            for tx in all_txs:
                # Check if linked to Checking Account
                # Purchase/Check/BillPayment have 'AccountRef'
                # JournalEntry has lines with AccountRef
                
                is_checking = False
                account_ref = tx.get("AccountRef", {}).get("value")
                if account_ref == checking_id:
                    is_checking = True
                
                # For JournalEntry, check lines?
                if tx.get("domain") == "QBO" and "JournalEntry" in str(tx): # weak check
                     # logic for JE
                     pass

                # Search for Pam/Seitz regardless of account first, then print if account matches
                blob = str(tx).lower()
                if "pam" in blob or "seitz" in blob:
                    found_count += 1
                    amt = tx.get("TotalAmt", "Unknown")
                    date = tx.get("TxnDate", "?")
                    type_ = tx.get("PaymentType", tx.get("TxnType", "Unknown"))
                    # Try to get entity name
                    entity = tx.get("EntityRef", {}).get("name", "Unknown")
                    if entity == "Unknown":
                        # Check Payee in BillPayment
                        entity = tx.get("VendorRef", {}).get("name", "Unknown")

                    print(f"\nMATCH FOUND!")
                    print(f"ID: {tx['Id']}")
                    print(f"Type: {type_}")
                    print(f"Date: {date}")
                    print(f"Amount: {amt}")
                    print(f"Entity/Payee: {entity}")
                    print(f"Is Checking Account: {is_checking} (AccountRef: {account_ref})")
                    print(f"Description/Memo: {tx.get('PrivateNote', '')}")
                    # Print Line Items if useful
                    for line in tx.get('Line', []):
                        desc = line.get('Description', '')
                        line_amt = line.get('Amount', '')
                        if desc:
                            print(f"  - Line: {desc} (${line_amt})")
            
            if found_count == 0:
                print("\nNo transactions found matching 'Pam' or 'Seitz' in the Checking Account recent history.")

        loop.run_until_complete(run())

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
